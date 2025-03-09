import streamlit as st
import os
import json
import logging
import re
from ai import generate_npc, generate_shop , generate_location 
from pathlib import Path
import requests
import chromadb
from embedding_management import list_embeddings, remove_embedding, add_embedding, retrieve_relevant_embeddings, generate_ai_response, pull_github_vault, reembed_modified_files

# Configure logging
logging.basicConfig(level=logging.INFO)

# Default cart structure
DEFAULT_CART_STRUCTURE = {"NPCs": [], "Shops": [], "Locations": [], "Encounters": [], "Dungeons": [], "Quests": []}

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

@handle_exception
def add_to_cart_button(category, item_key):
    """Reusable 'Add to Cart' button for any item.
    
    Args:
        category (str): The category to store the item in (e.g., "NPCs", "Quests").
        item_key (str): A unique key for session storage (e.g., "generated_npc").
    """
    if item_key not in st.session_state:
        st.session_state[item_key] = None  

    # Ensure item exists and is a dictionary
    item = st.session_state[item_key]
    if item and isinstance(item, str):  # Convert strings to dictionaries
        item = {"name": "Unnamed", "content": item}

    if item:  # Ensure there's content before saving
        if st.button(f"➕ Add {category[:-1]} to Cart", key=f"add_{category.lower()}"):
            cart = load_cart()
            cart[category].append({"name": item.get("name", "Unnamed"), "content": item})
            save_cart(cart)
            st.success(f"✅ {category[:-1]} added to cart!")
            st.session_state[item_key] = None  # Clear after adding
    else:
        st.warning(f"⚠️ Generate a {category[:-1]} first before adding to the cart.")

CONFIG_PATH = "config.yaml"

@handle_exception
def load_config():
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)

@handle_exception
def save_config(config):
    with open(CONFIG_PATH, "w") as file:
        yaml.safe_dump(config, file)

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
    if st.button("📋 Folder Embedding Management", key="embedding_management_sidebar"):
        navigate_to("Folder Embedding Management")  
    if st.button("📚 Embedding Process", key="embedding_sidebar"):
        navigate_to("Embedding Process")


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

        else:
            st.warning(f"No files found in {selected_category}.")
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

    # Use the reusable button
    add_to_cart_button("Dungeons", "generated_dungeon", st.session_state["generated_dungeon"])

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
    st.title("🧠 Campaign Assistant")
    render_sidebar()
    user_query = st.text_input("Ask something about your campaign:")
    if st.button("Get AI Answer"):
        if "openai_api_key" in st.session_state and st.session_state.openai_api_key:
            response = generate_ai_response(user_query, st.session_state.openai_api_key)
            st.markdown("### 🤖 AI Response")
            st.write(response)
        else:
            st.error("⚠️ Please enter your OpenAI API key in settings.")
    
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

    # Use the reusable button
    add_to_cart_button("Shops", "generated_shop", st.session_state["generated_shop"])


def render_create_location_page():
    st.title("📍 Create Location")
    render_sidebar()
    location_prompt = st.text_area("What do you already know about this location? (Optional)")
    if st.button("Generate Location", key="generate_location_button"):
        location = generate_location(st.session_state.openai_api_key, location_prompt)  
        st.session_state.generated_location = location  
        st.text_area("Generated Location:", location, height=250)

    # Use the reusable button
    add_to_cart_button("Locations", "generated_location", st.session_state["generated_location"])


def render_generate_npc_page():
    st.title("🧙 Generate NPC")
    render_sidebar()
    
    npc_prompt = st.text_area("What do you already know about this NPC? (Optional)")
    
    # Ensure NPC storage exists in session state
    if "generated_npc" not in st.session_state:
        st.session_state["generated_npc"] = None  

    # Generate NPC and store in session
    if st.button("Generate NPC", key="generate_npc_button"):
        npc = generate_npc(st.session_state.openai_api_key, npc_prompt)  
        if npc:  
            st.session_state["generated_npc"] = npc  # Store NPC in session
            st.text_area("Generated NPC:", npc, height=250)  
        else:
            st.error("❌ NPC generation failed. Try again.")

    # Use the reusable button
    add_to_cart_button("NPCs", "generated_npc", st.session_state["generated_npc"])

def render_folder_management_page():
    st.title("📋 Folder Embedding Management")
    
    if st.button("🔄 Pull from GitHub Vault"):
        pull_github_vault()
    
    config = load_config()
    folders = config.get("folders_to_embed", [])
    
    st.subheader("📂 Current Folders to Embed:")
    for folder in folders:
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(folder)
        if col2.button("❌ Remove", key=folder):
            folders.remove(folder)
            config["folders_to_embed"] = folders
            save_config(config)
            st.experimental_rerun()
    
    new_folder = st.text_input("➕ Add a new folder:")
    if st.button("Add Folder"):
        if new_folder and new_folder not in folders:
            folders.append(new_folder)
            config["folders_to_embed"] = folders
            save_config(config)
            st.experimental_rerun()

def render_embedding_page():
    st.title("📚 Embedding Process")
    st.write("Manage campaign embeddings stored in ChromaDB.")
    
    st.subheader("🔄 Re-Embed Modified Files")
    if st.button("Re-Embed Selected Folders"):
        st.info("Processing embeddings...")
        reembed_modified_files()
        st.success("✅ Embedding completed!")
    
    st.subheader("📋 View Stored Embeddings")
    embeddings = list_embeddings()
    if embeddings["ids"]:
        for i, (eid, doc) in enumerate(zip(embeddings["ids"], embeddings["documents"])):
            with st.expander(f"📄 {eid}"):
                st.write(doc)
                if st.button(f"❌ Remove {eid}", key=f"remove_{i}"):
                    remove_embedding(eid)
                    st.rerun()
    else:
        st.info("ℹ️ No embeddings stored yet.")
    
    st.subheader("➕ Add New Embedding")
    uploaded_file = st.file_uploader("Upload a file to embed", type=["txt", "md"])
    if uploaded_file is not None:
        new_text = uploaded_file.getvalue().decode("utf-8")
    else:
        new_text = st.text_area("Or enter text to embed:")
    
    metadata_input = st.text_input("Enter metadata (optional, JSON format):", "{}")
    if st.button("Add Embedding"):
        try:
            metadata = json.loads(metadata_input)
            if not isinstance(metadata, dict):
                metadata = {"source": "manual"}  # Ensure metadata is a dictionary
            add_embedding(new_text, metadata)
            st.rerun()
        except json.JSONDecodeError:
            st.error("❌ Invalid metadata JSON format.")

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
    "Worldbuilding and Lore": render_worldbuilding_page,
    "Folder Embedding Management": render_folder_management_page,
    "Embedding Process": render_embedding_page
    
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
