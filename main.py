import streamlit as st
import os
import json
import logging
import re
from dotenv import load_dotenv
from ai import generate_npc, generate_shop , generate_location 
from pathlib import Path
from obsidian import get_authorization_url
import requests
from urllib.parse import urlparse, parse_qs
from obsidian import exchange_code_for_tokens
import dropbox
from dropbox.exceptions import AuthError

# Configure logging
logging.basicConfig(level=logging.INFO)

# Default cart structure
DEFAULT_CART_STRUCTURE = {"NPCs": [], "Shops": [], "Locations": [], "Encounters": [], "Dungeons": [], "Quests": []}

# Load environment variables
load_dotenv()

def handle_oauth_callback():
    """Check if Dropbox authorization code exists in the URL and exchange it for tokens."""
    query_params = st.experimental_get_query_params()

    if "code" in query_params:
        auth_code = query_params["code"][0]  # Extract the auth code
        st.success("✅ Authorization code received!")

        # Exchange the authorization code for access/refresh tokens
        tokens = exchange_code_for_tokens(auth_code)
        if tokens:
            st.success("✅ Dropbox connected successfully! You can now upload and retrieve files.")
            st.session_state["dropbox_authenticated"] = True
        else:
            st.error("❌ Failed to authenticate with Dropbox.")

st.title("Connect to Dropbox")

# Generate the Dropbox login link
auth_url = get_authorization_url()
st.markdown(f"[🔗 Click here to connect Dropbox]({auth_url})")

# Handle OAuth callback
handle_oauth_callback()

def upload_to_dropbox(file_path, dropbox_folder):
    """Upload a file to Dropbox, auto-refreshing the token if needed."""
    global DROPBOX_ACCESS_TOKEN
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        with open(file_path, "rb") as f:
            dbx.files_upload(f.read(), f"{dropbox_folder}/{os.path.basename(file_path)}", mode=dropbox.files.WriteMode("overwrite"))
    except AuthError:
        print("🔄 Access token expired, refreshing...")
        DROPBOX_ACCESS_TOKEN = refresh_access_token()
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        with open(file_path, "rb") as f:
            dbx.files_upload(f.read(), f"{dropbox_folder}/{os.path.basename(file_path)}", mode=dropbox.files.WriteMode("overwrite"))

# Exception handling decorator
def handle_exception(func):
    """Centralized error handling decorator."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (FileNotFoundError, ValueError) as e:
            st.error(f"⚠️ Error: {str(e)}")
            logging.error(f"Error in {func.__name__}: {e}")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {e}")
            logging.error(f"Unexpected error in {func.__name__}: {e}")
        return None
    return wrapper

@handle_exception
def initialize_session_state():
    if not getattr(st.session_state, "initialized", False):
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
            "initialized": True
        }
        st.session_state.update(session_defaults)

initialize_session_state()

# Load the cart from JSON (ensure persistence)
CART_FILE = Path("cart.json")

@handle_exception
def load_cart():
    if CART_FILE.exists():
        with open(CART_FILE, "r") as file:
            return json.load(file)
    return {"NPCs": [], "Shops": [], "Locations": [], "Encounters": [], "Dungeons": [], "Quests": []}
   
if "cart" not in st.session_state:
    st.session_state["cart"] = load_cart()  # Assign loaded cart

@handle_exception
def save_cart(cart):
    st.session_state["cart"] = cart  # Keep session in sync
    with open(CART_FILE, "w") as file:
        json.dump(cart, file, indent=4)
        
@handle_exception
def save_to_vault(category, item):
    """Save content to the vault only when manually confirmed from the cart page.
    
    Args:
        category (str): The category under which the item will be saved.
        item (str): The content that needs to be saved to the vault.
    """
    if "selected_content_to_save" not in st.session_state:
        st.session_state["selected_content_to_save"] = ""

    if st.session_state["selected_content_to_save"] and st.session_state.get("page") == "Cart":
        st.subheader("Modify Selected Content Before Saving")
        edited_content = st.text_area("Edit before saving to vault:", 
                                       st.session_state["selected_content_to_save"], height=300)

        if st.button("📁 Save to Vault", key="send_to_vault"):
            if edited_content.strip():
                # Save the item
                save_content_to_vault(category, edited_content)

                # Remove it from the cart after saving
                cart = load_cart()
                if item in cart.get(category, []):
                    cart[category].remove(item)
                    save_cart(cart)

                st.success(f"✅ '{item}' saved to the vault!")
                st.session_state["selected_content_to_save"] = ""
            else:
                st.warning("⚠️ Content is empty! Please modify before sending to vault.")

@handle_exception
def save_content_to_vault(category, content):
    """Handles the actual saving of content to the Obsidian vault (or cloud storage).
    
    Args:
        category (str): The category under which the content will be saved.
        content (str): The content to be saved.
    """
    vault_path = Path(f"obsidian_vault/{category}.md")
    vault_path.parent.mkdir(parents=True, exist_ok=True)

    with open(vault_path, "a") as file:
        file.write(f"\n---\n{content}\n")

    st.success(f"✅ Successfully saved under {category} in the vault!")

@handle_exception
def add_to_cart(category, session_key):
    """Add generated content to the cart without saving to vault, ensuring correct naming."""
    if st.session_state.get(session_key):
        item = st.session_state[session_key]

        # Ensure the cart category exists
        if category not in st.session_state["cart"]:
            st.session_state["cart"][category] = []

        # Avoid duplicates
        if item not in st.session_state["cart"][category]:
            st.session_state["cart"][category].append(item)
            save_cart(st.session_state["cart"])  # Save the updated cart
            st.success(f"✅ Added to {category} in the cart!")
        else:
            st.warning(f"⚠️ This item is already in {category}!")
            
def navigate_to(page_name):
    """Navigate to a specific page and persist state."""
    if page_name in PAGES:
        st.session_state.page = page_name
        st.query_params["page"] = page_name
        st.rerun()
    else:
        st.warning(f"⚠️ Invalid page: {page_name}")
        st.session_state.page = "Main Menu"
        st.rerun()
        
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
    st.title("Enter Your API Keys")

    # OpenAI API Key input
    openai_key = st.text_input("Enter OpenAI API Key:", type="password")

    # Dropbox OAuth login link
    st.subheader("Connect to Dropbox")
    auth_url = get_authorization_url()
    st.markdown(f"[🔗 Click here to connect Dropbox]({auth_url})")

    if st.button("Login"):
        if openai_key:
            st.session_state["openai_api_key"] = openai_key
            st.session_state["authenticated"] = True  # Ensuring it's saved before rerun
            st.session_state["page"] = "Main Menu"  # Redirect to Main Menu after login
            st.success("✅ Access Granted!")
            st.stop()  # Prevents execution from continuing before rerun
        else:
            st.error("❌ Please enter your OpenAI API Key.")

# Authentication & Navigation Check: Redirect to Main Menu if authenticated
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "page" not in st.session_state:
    st.session_state["page"] = "API Key"

if not st.session_state["authenticated"]:
    render_api_key_page()
    st.stop()
    handle_oauth_callback()
else:
    st.session_state["page"] = "Main Menu"  # Redirect to Main Menu if authenticated


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
    
                    # Save to Vault after reviewing
                    if st.button("📁 Save to Vault", key="send_to_vault"):
                        if edited_content.strip():
                            base_filename = f"{selected_category}_{selected_file}"[:50]  # Limit to 50 chars
                            safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', base_filename) + ".md"
                            save_to_vault(selected_category, edited_content)  # Saves reviewed content to vault
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
        add_to_cart("NPCs", "generated_npc")

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
    """Render the correct page based on session state."""
    query_params = st.query_params
    requested_page = query_params.get("page", "Main Menu")
    if isinstance(requested_page, list):
        requested_page = requested_page[0]
    st.session_state.page = requested_page if requested_page in PAGES else "Main Menu"
    PAGES[st.session_state.page]()

if __name__ == "__main__":
    render_page()
