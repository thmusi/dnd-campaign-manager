import streamlit as st
import os
import json
import logging
import re
from dotenv import load_dotenv
from google.oauth2 import service_account  # Import the correct credentials module

# Import AI and Obsidian functionalities
from ai import (
    generate_npc,
    generate_shop,
    generate_location,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Default cart structure
DEFAULT_CART_STRUCTURE = {
    "NPCs": [],
    "Shops": [],
    "Locations": [],
    "Encounters": [],
    "Dungeons": [],
    "Quests": []
}

# Load environment variables
load_dotenv()

# Define Render secret file path
GOOGLE_CREDENTIALS_PATH = "/etc/secrets/google_credentials"

def load_google_credentials():
    """Loads Google Drive API credentials securely for both Streamlit Cloud & Render"""
    
    # 1️⃣ If running on Streamlit Cloud, use st.secrets
    if "google_drive" in st.secrets:
        credentials_dict = json.loads(json.dumps(st.secrets["google_drive"]))  # Convert TOML to JSON
        return service_account.Credentials.from_service_account_info(credentials_dict)

    # 2️⃣ If running on Render, read from the secret file
    elif os.path.exists(GOOGLE_CREDENTIALS_PATH):
        with open(GOOGLE_CREDENTIALS_PATH, "r") as f:
            credentials_json = f.read().strip()
        credentials_dict = json.loads(credentials_json)  # Convert back to JSON
        credentials_dict["private_key"] = credentials_dict["private_key"].replace("\\n", "\n")  # Fix newlines
        return service_account.Credentials.from_service_account_info(credentials_dict)

    else:
        st.error("❌ Google Drive credentials not found in Streamlit secrets or Render secret files!")
        st.stop()

# Load credentials dynamically
credentials = load_google_credentials()
st.success("✅ Google Drive authentication successful!")

# Exception handling decorator
def handle_exception(func):
    """Centralized error handling decorator."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            st.error("⚠️ File not found. Please check the file path.")
            logging.error(f"File error in {func.__name__}: {e}")
        except ValueError as e:
            st.error("⚠️ Invalid value encountered. Please check your input.")
            logging.error(f"Value error in {func.__name__}: {e}")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {e}")
            logging.error(f"Error in {func.__name__}: {e}")
        return None
    return wrapper

@handle_exception
def initialize_session_state():
    if not st.session_state.get("initialized", False):
        session_defaults = {
            "openai_api_key": None,
            "cart": DEFAULT_CART_STRUCTURE.copy(),
            "page": "API Key",
            "selected_content_to_save": None,
            "selected_category": "",
            "selected_file": "",
            "generated_npc": None,
            "generated_shop": None,
            "generated_location": None,
            "generated_dungeon": None,
            "generated_encounter": None,
            "initialized": True
        }

        for key, value in session_defaults.items():
            setattr(st.session_state, key, value)

initialize_session_state()

@handle_exception
def save_cart():
    """Save the current cart to a structured local file."""
    st.session_state.cart = {**DEFAULT_CART_STRUCTURE, **st.session_state.cart}

    with open("cart.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.cart, f, indent=4)
    
    st.success("✅ Cart saved with structured format!")

@handle_exception
def save_to_vault(category, item):
    """Save content to the vault only when manually confirmed from the cart page."""
    if st.session_state.page == "Cart":
        save_cart()
        st.success(f"✅ {item} saved to the vault!")

@handle_exception
def load_cart():
    file_path = "cart.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            st.session_state.cart = json.load(f)
    else:
        st.session_state.cart = DEFAULT_CART_STRUCTURE.copy()
        st.success("✅ Cart loaded with structured format!")

if "cart" not in st.session_state:
    load_cart()

if st.session_state.selected_content_to_save and st.session_state.page == "Cart":
    st.subheader("Modify Selected Content Before Saving")
    edited_content = st.text_area("Edit before saving to vault:", st.session_state["selected_content_to_save"], height=300)

    if st.button("📁 Save to Vault", key="send_to_vault"):
        if edited_content.strip():
            save_to_vault(st.session_state["selected_category"], edited_content)
            st.success(f"✅ Saved {st.session_state['selected_file']} to the vault!")
            st.session_state["selected_content_to_save"] = None  # Clear after saving
        else:
            st.warning("⚠️ Content is empty! Modify before sending to vault.")

def add_to_cart(category, session_key):
    """Add generated content to the cart without saving to vault, ensuring correct naming."""
    if st.session_state.get(session_key):
        item = st.session_state[session_key]
        
        # Extract NPC Name (or Shop/Location Name) if available
        name_match = re.search(r"\*\*Nom\*\* ?: (.+)", item) if isinstance(item, str) else None
        item_name = name_match.group(1) if name_match else f"New {category[:-1]}"

        if st.button(f"🛒 Add {item_name} to Cart", key=f"add_{session_key}_to_cart"):
            st.session_state.cart[category] = st.session_state.cart.get(category, [])
            st.session_state.cart[category].append(item)
            save_cart()
            st.success(f"✅ {item_name} added to {category} in the cart!")

def navigate_to(page_name):
    """Ensure only valid pages are set."""
    if page_name in PAGES:
        st.session_state.page = page_name
    else:
        st.warning(f"⚠️ Attempted to navigate to invalid page: {page_name}")
        st.session_state.page = "Main Menu"  # Redirect to Main Menu instead

def render_sidebar():
    """Render the sidebar navigation menu."""
    with st.sidebar:
        st.title("Navigation")
        if st.session_state.page == "API Key":
            return
        if st.button("🏠 Home", key="home_sidebar"):
            navigate_to("Main Menu")
        if st.button("🛒 Cart", key="cart_sidebar"):
            navigate_to("Cart")
        st.markdown("---")
        if st.session_state.page != "Main Menu":
            render_main_menu_buttons()

def render_main_menu_buttons():
    """Render navigation buttons on the Main Menu page."""
    st.subheader("Main Menu Options")
    if st.button("🧙 Create NPC", key="generate_npc"):
        navigate_to("Generate NPC")
    if st.button("🏪 Create Shop", key="generate_shop"):
        navigate_to("Create Shop")
    if st.button("📍 Generate a Location", key="create_location"):
        navigate_to("Create Location")
    if st.button("📖 Adapt Chapter to Campaign", key="adapt_chapter"):
        navigate_to("Adapt Chapter")
    if st.button("🧠 Campaign Assistant", key="campaign_assistant"):
        navigate_to("Campaign Assistant")
    if st.button("⚔️ Encounter Generator", key="encounter_generator"):
        navigate_to("Encounter Generator")
    if st.button("🏰 Dungeon Generator", key="dungeon_generator"):
        navigate_to("Dungeon Generator")
    if st.button("📜 Quest Generator", key="quest_generator"):
        navigate_to("Quest Generator")
    if st.button("🌍 Worldbuilding", key="worldbuilding"):
        navigate_to("Worldbuilding")
    if st.button("🗒 Session Management", key="session_management"):
        navigate_to("Session Management")

# Apply custom styling to buttons
st.markdown(
    """
    <style>
    .stButton>button {
        width: 100%;
        padding: 10px;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Page Functions
def render_api_key_page():
    st.title("Enter Your OpenAI API Key")

    openai_key = st.text_input("Enter OpenAI API Key:", type="password")
    if st.button("Login"):
        if openai_key:
            st.session_state["authenticated"] = True
            st.session_state["openai_api_key"] = openai_key
            st.success("Access Granted!")
            st.experimental_rerun()
        else:
            st.error("Please enter your OpenAI API Key.")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    render_api_key_page()
    st.stop()

def render_main_menu_page():
    st.title("Welcome to the DnD Campaign Manager")
    st.markdown("Select an option from the buttons below to get started.")
    render_main_menu_buttons()
    render_sidebar()

def render_cart_page():
    st.title("🛒 Your Cart")
    st.markdown("Manage your saved content before sending it to the vault.")
    render_sidebar()
    categories = list(st.session_state.cart.keys())
    
    if categories:
        selected_category = st.selectbox("📂 Select Folder", categories)
            
        if selected_category in st.session_state.cart:
            files = st.session_state.cart[selected_category]
            if files:
                selected_file = st.selectbox(f"📜 Files in {selected_category}", files)
                    
                if selected_file:
                    st.markdown("### 📖 Preview")
                    st.markdown(selected_file)
    
                    # Modify Content Directly in Cart
                    st.subheader("Modify Selected Content")
                    edited_content = st.text_area("Edit before saving:", selected_file, height=300)
    
                    # ✅ Save to Vault after reviewing
                    if st.button("📁 Save to Vault", key="send_to_vault"):
                        if edited_content.strip():
                            base_filename = f"{selected_category}_{selected_file}"[:50]  # Limit to 50 chars
                            safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', base_filename) + ".md"
                            save_to_vault(selected_category, edited_content)  # ✅ Saves reviewed content to vault
                        else:
                            st.warning("Content is empty! Modify before sending to vault.")
            else:
                st.warning(f"No files found in {selected_category}.")
        else:
            st.warning("Selected category does not exist.")
    else:
        st.warning("Your cart is empty.")

def render_worldbuilding_page():
    st.title("🌍 Worldbuilding Expansion & Lore")
    st.subheader("🌍 Worldbuilding Expansion")
    st.write("Auto-fill lore and expand world details.")
    st.button("Generate World Lore", key="generate_world_lore_button")

def render_session_management_page():
    st.title("🗒 Session Management")
    render_sidebar()
    st.write("Tools for session intros and note assistance.")
    st.text_input("Session Details (e.g., S01):", key="session_details_input")
    st.button("Load Session History", key="load_session_history_button")

def render_quest_generator_page():
    st.title("📜 Quest Generator")
    render_sidebar()
    st.write("Generate a quest based on input details.")
    st.text_input("Quest Prompt:", key="quest_prompt_input")
    st.button("Generate Quest", key="generate_quest_button")
  
def render_dungeon_generator_page():
    st.title("🏰 Dungeon Generator")
    render_sidebar()
    st.write("Enter dungeon details and generate a full layout.")
    st.number_input("Party Size", min_value=1, step=1, max_value=20, key="party_size_input")
    st.number_input("Party Level", min_value=1, step=1, max_value=20, key="party_level_input")
    dungeon_prompt = st.text_area("Dungeon Prompt:", key="dungeon_prompt_input")
    if st.button("Generate Dungeon", key="generate_dungeon_button"):
        # Placeholder logic for dungeon generation
        st.session_state.generated_dungeon = "A mysterious dungeon layout appears..."
        st.text_area("Generated Dungeon:", st.session_state.generated_dungeon, height=250)
          
    if getattr(st.session_state, "generated_dungeon", None):
        if st.button("🗺️ Generate Grid Battle Map", key="generate_battle_map"):
            import numpy as np
            import matplotlib.pyplot as plt
            import io
            import base64

            grid_size = 10  # Adjust for larger maps
            dungeon_map = np.random.choice([0, 1], size=(grid_size, grid_size), p=[0.7, 0.3])

            fig, ax = plt.subplots()
            ax.imshow(dungeon_map, cmap="gray_r", interpolation="nearest")
            ax.set_xticks([])
            ax.set_yticks([])

            # Save to a buffer
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)
                
            # Create a downloadable link
            b64 = base64.b64encode(buf.getvalue()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="battle_map.png">📥 Download Battle Map</a>'

            st.pyplot(fig)
            st.markdown(href, unsafe_allow_html=True)
            st.success("Battle map generated! Click the link above to download.")

def render_encounter_generator_page():
    st.title("⚔️ Encounter Generator")
    render_sidebar()
    st.write("Generate encounters based on party size and details.")
    st.number_input("Party Size", min_value=1, step=1, max_value=20, key="party_size_input")
    st.number_input("Party Level", min_value=1, step=1, max_value=20, key="party_level_input")
    st.text_input("Custom Encounter Prompt:", key="custom_encounter_input")
    st.button("Generate Encounter", key="generate_encounter_button")

def render_campaign_assistant_page():
    st.title("📖 Campaign Assistant")
    render_sidebar()
    st.write("Ask me anything!")
    st.text_input("Enter your query:", key="query_input")
    st.button("Submit Query", key="submit_query")

def render_adapt_chapter_page():
    st.title("📖 Adapt Chapter to Campaign")
    render_sidebar()
    st.write("Modify your campaign text dynamically.")
    col1, col2, col3 = st.columns(3)
        
    with col1:
        original_chapter = st.text_area("Original Chapter", height=500)
        if st.button("Load", key="load_chapter"):
            # Load functionality would go here
            pass
        
    with col2:
        edits_input = st.text_area("Edits Input", height=500)
        if st.button("What do you think?", key="feedback_button"):
            # Feedback functionality would go here
            pass
        
    with col3:
        ai_output = st.text_area("AI Output", height=500)

def render_create_shop_page():
    st.title("🏪 Create Shop")
    render_sidebar()
    shop_type = st.selectbox("Select Shop Type", [
     "General Store", "Blacksmith", "Alchemy Shop", "Magic Shop", "Tavern", 
     "Jewelry Store", "Weapon Shop", "Armorer", "Fletcher", "Bookstore", "Stable",
     "Enchanter", "Herbalist", "Bakery", "Tailor",  
    ])  
    
    shop_prompt = st.text_area("What do you already know about this shop? (Optional)")
    if st.button("Generate Shop", key="generate_shop_button"):
         shop = generate_shop(st.session_state.openai_api_key, shop_type, shop_prompt)  
         st.session_state.generated_shop = shop  
         st.text_area(f"Generated {shop_type}:", shop, height=250)

    if getattr(st.session_state, "generated_shop", None):
        add_to_cart("Shops", "generated_shop")

def render_create_location_page():
    st.title("📍 Create Location")
    render_sidebar()
    location_prompt = st.text_area("What do you already know about this location? (Optional)")
    if st.button("Generate Location", key="generate_location_button"):
        location = generate_location(st.session_state.openai_api_key, location_prompt)  
        st.session_state.generated_location = location  
        st.text_area("Generated Location:", location, height=250)

    if getattr(st.session_state, "generated_location", None):
        add_to_cart("Locations", "generated_location")
        st.success("Added to Cart!")

def render_generate_npc_page():
    st.title("🧙 Generate NPC")
    render_sidebar()
    npc_prompt = st.text_area("What do you already know about this NPC? (Optional)")
        
    if st.button("Generate NPC", key="generate_npc_button"):
        npc = generate_npc(st.session_state.openai_api_key, npc_prompt)  
        st.session_state.generated_npc = npc  
        st.text_area("Generated NPC:", npc, height=250)  
      
    if getattr(st.session_state, "generated_npc", None):
        add_to_cart("NPCs", "generated_npc")  # ✅ Fixed indentation

# Dynamic Page Rendering Dictionary
PAGES = {
    "API Key": render_api_key_page,
    "Main Menu": render_main_menu_page,
    "Cart": render_cart_page,
    "Session Management": render_session_management_page,
    "Quest Generator": render_quest_generator_page,
    "Dungeon Generator": render_dungeon_generator_page,
    "Encounter Generator": render_encounter_generator_page,
    "Campaign Assistant": render_campaign_assistant_page,
    "Adapt Chapter": render_adapt_chapter_page,
    "Create Shop": render_create_shop_page,
    "Create Location": render_create_location_page,
    "Generate NPC": render_generate_npc_page,
    "Worldbuilding and Lore": render_worldbuilding_page
}

def render_page():
    if "page" not in st.session_state:
        st.session_state.page = "API Key"
    
    if st.session_state.page in PAGES:
        PAGES[st.session_state.page]()
    else:
        st.warning("⚠️ Page not found, redirecting to Main Menu...")
        st.session_state.page = "Main Menu"
        render_main_menu_page()

if __name__ == "__main__":
    render_page()
