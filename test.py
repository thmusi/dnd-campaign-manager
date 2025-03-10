import streamlit as st
import obsidian  # Ensure full module import for debugging
from obsidian import list_drive_files, upload_file, download_file, save_ai_generated_content
from obsidian import write_note, list_campaign_files
import ssl
import time
import os
import re
import json
import logging
from dotenv import load_dotenv

# Import AI and Obsidian functionalities
from ai import (
    generate_npc,
    generate_shop,
    generate_location,
    modify_campaign_chapter,
    ai_search_campaign_notes,
)
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Initialize Google Drive service
def initialize_drive_service():
    try:
        credentials_json = st.secrets["GOOGLE_DRIVE_API_CREDENTIALS"]
        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        return build('drive', 'v3', credentials=credentials)
    except KeyError:
        st.error("Google Drive API credentials are missing in Streamlit Secrets.")
        logging.error("Missing GOOGLE_DRIVE_API_CREDENTIALS in Streamlit Secrets.")
        return None
    except json.JSONDecodeError:
        st.error("Failed to decode Google Drive API credentials.")
        logging.error("Invalid JSON format for GOOGLE_DRIVE_API_CREDENTIALS.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while initializing Google Drive: {e}")
        logging.error(f"Unexpected error: {e}")
        return None


drive_service = initialize_drive_service()


def cached_list_drive_files():
    try:
        return list_drive_files()
    except Exception as e:
        logging.error(f"Error listing Drive files: {e}")
        st.error("Failed to retrieve Google Drive files.")
        return []

# Initialize session state
if "campaign_files" not in st.session_state:
    st.session_state["campaign_files"] = cached_list_drive_files()

st.write("Available Campaign Files:", st.session_state["campaign_files"])

def initialize_session_state():
    """Initialize session state variables."""
    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    if "cart" not in st.session_state:
        st.session_state.cart = {}
    if "page" not in st.session_state:
        st.session_state.page = "API Key"

initialize_session_state()

    """Save the current cart to Google Drive with error handling."""
    try:
        json_data = json.dumps(st.session_state.cart)
        with open("cart.json", "w", encoding="utf-8") as f:
            f.write(json_data)
        upload_file("cart.json")

        st.success("Cart saved to Google Drive!")
        logging.info("Cart saved successfully to Google Drive.")
     except OSError as e:
        st.error(f"File operation error: {e}")
        logging.error(f"File operation error: {e}")

    except Exception as e:
        st.error(f"Failed to save cart: {e}")
        logging.error(f"Error saving cart: {e}")

def load_cart():
    """Load the cart from Google Drive with file validation and retry mechanism for SSL errors."""
    try:
        file_id = None
        files = list_drive_files()

        # Find the cart.json file in Google Drive
        for file in files:
            if file["name"] == "cart.json":
                file_id = file["id"]
                break

        if not file_id:
            st.warning("No saved cart found in Google Drive.")
            return

        # Retry download if SSL error occurs
        attempts = 3
        for attempt in range(attempts):
            try:
                download_file(file_id, "cart.json")
                break  # If successful, exit loop
            except ssl.SSLError:
                st.warning(f"SSL error, retrying... ({attempt+1}/{attempts})")
                time.sleep(2)  # Wait before retrying
        else:
            st.error("Failed to download cart.json after multiple attempts.")
            return

        # ✅ Ensure the file exists and is not empty
        if not os.path.exists("cart.json") or os.stat("cart.json").st_size == 0:

        if not os.path.exists("cart.json"):
            st.error("Downloaded cart.json is missing or empty. Try saving again.")
            
        # Read the file safely
        with open("cart.json", "r", encoding="utf-8") as f:
            st.session_state.cart = json.load(f)

        st.success("Cart loaded from Google Drive!")

    except json.JSONDecodeError:
        st.error("Failed to decode cart data. Please check the file format.")
    except ssl.SSLError as e:
        st.error(f"SSL error: {e}")
    except Exception as e:
        st.error(f"Error loading cart: {e}")


def save_to_vault(content, filename="generated_content.md"):
    """Saves the modified content to the user's Obsidian-Google Drive vault only when manually triggered."""
    vault_path = "obsidian_vault"
    os.makedirs(vault_path, exist_ok=True)  # Ensure directory exists
    
    # Ensure filename has only one .md extension
    if not filename.endswith(".md"):
        filename += ".md"
    
    file_path = os.path.join(vault_path, filename)

    # Save locally before upload
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    if drive_service:  # Ensure drive_service is initialized

    st.success(f"✅ File saved successfully to Google Drive: {filename}")
    else:
        st.error("Drive service not initialized. File not saved.")

# Ensure saving to vault happens only when a button is pressed
if st.session_state.get("selected_content_to_save"):
    if st.button("📁 Save to Vault")
        category = st.session_state.get("selected_category", "generated_content")
        
        content_data = st.session_state.get("selected_content_to_save", "")

        # Extract a meaningful filename based on content type
        if category in content_data:
            base_filename = content_data[category].get("name", f"{category}_content")
        else:
            base_filename = f"{category}_{st.session_state.get('selected_file', 'content')}"

        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', base_filename) + ".md"
        save_to_vault(content_data, filename=safe_filename)
        st.session_state["selected_content_to_save"] = None  # Clear after saving

def navigate_to(page_name):
    """Change the current page in the session state."""
    st.session_state.page = page_name

def render_sidebar():
    """Render the sidebar navigation menu."""
    with st.sidebar:
        st.title("Navigation")

        # Check the current page and render buttons accordingly
        if st.session_state.page == "API Key":
            return  # No sidebar for API Key page
        if st.button("🏠 Home", key="home_sidebar"):
            navigate_to("Main Menu")
        if st.button("🛒 Cart", key="cart_sidebar"):
            navigate_to("Cart")
        st.markdown("---")
        if st.session_state.page != "Main Menu":  
            if st.button("🧙 Create NPC", key="generate_npc"):
                navigate_to("Generate NPC")
            if st.button("🏪 Create Shop", key="generate_shop"):
                navigate_to("Create Shop")
            if st.button("📍 Create Location", key="create_location"):
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

def render_main_menu_buttons():
    """Render navigation buttons on the Main Menu page."""
    st.subheader("Main Menu Options")
    if st.button("🧙 Create NPC", key="generate_npc"):
        navigate_to("Generate NPC")
    if st.button("🏪 Create Shop", key="generate_shop"):
        navigate_to("Create Shop")
    if st.button("📍 Create Location", key="create_location"):
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

# Main application logic
def main():
    """Main function to run the Streamlit application."""
    render_sidebar()
    load_cart()
    
    # Page rendering based on session state
    try:
    	if st.session_state.page == "API Key":
       		st.title("Enter your API Key")
       		
        	st.session_state.api_key = st.text_input("API Key", type="password")
        	if st.button("Submit", key="submit_api_key"):
            	if st.session_state.api_key:
                	st.success("API Key set!")
                	navigate_to("Main Menu")
            	else:
                	st.error("Please enter a valid API Key.")

    elif st.session_state.page == "Main Menu":
        st.title("Welcome to the DnD Campaign Manager")
        st.markdown("Select an option from the buttons below to get started.")
        render_main_menu_buttons()

    # Generate NPC
    elif st.session_state.page == "Generate NPC":
        st.title("🛡️ Generate an NPC")
        npc_prompt = st.text_area("What do you already know about this NPC? (Optional)")
        if st.button("Generate NPC"):
            npc = generate_npc(st.session_state.api_key, npc_prompt)  
            st.session_state.generated_npc = npc  
            st.text_area("Generated NPC:", npc, height=250)  

        if "generated_npc" in st.session_state:
            if st.button("🛒 Add to Cart"):
                st.session_state.cart["npc"] = st.session_state.cart.get("npc", [])  
                st.session_state.cart["npc"].append(st.session_state.generated_npc)
                save_cart()
                st.success("Added to Cart!")

    # Cart page rendering
    elif st.session_state.page == "Cart":
        st.title("🛒 Your Cart")
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
                        edited_content = st.text_area("Edit the selected content before saving:", selected_file, height=300)
                        
                        # Send to Vault
                        if st.button("Send to Vault"):
                            if edited_content.strip():
                                # ✅ Trim filename to avoid excessively long names
                                base_filename = f"{selected_category}_{selected_file}"[:50]  # Limit to 50 chars
                                safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', base_filename) + ".md"
                                save_to_vault(edited_content, filename=safe_filename)

                            else:
                                st.warning("Content is empty! Please modify before sending to vault.")
                else:
                    st.warning(f"No files found in {selected_category}.")
            else:
                st.warning("Selected category does not exist.")
        else:
            st.warning("Your cart is empty.")

    # Generate Location
    elif st.session_state.page == "Create Location":
        st.subheader("🏰 Generate a Location")
        location_prompt = st.text_area("What do you already know about this location? (Optional)")
        if st.button("Generate Location"):
            location = generate_location(st.session_state.api_key, location_prompt)  
            st.session_state.generated_location = location  
            st.text_area("Generated Location:", location, height=250)

        if "generated_location" in st.session_state:
            if st.button("🛒 Add to Cart"):
                st.session_state.cart["location"] = st.session_state.cart.get("location", [])  
                st.session_state.cart["location"].append(st.session_state.generated_location)
                save_cart()
                st.success("Added to Cart!")

    # Generate Shop
    elif st.session_state.page == "Create Shop":
        st.subheader("🛒 Generate a Shop")
        shop_type = st.selectbox("Select Shop Type", [
            "General Store", "Blacksmith", "Alchemy Shop", "Magic Shop", "Tavern", 
            "Jewelry Store", "Weapon Shop", "Armorer", "Fletcher", "Bookstore", "Stable",
            "Enchanter", "Herbalist", "Bakery", "Tailor",
        ])
        shop_prompt = st.text_area("What do you already know about this shop? (Optional)")
        if st.button("Generate Shop"):
            shop = generate_shop(st.session_state.api_key, shop_type, shop_prompt)  
            st.session_state.generated_shop = shop  
            st.text_area(f"Generated {shop_type}:", shop, height=250)

        if "generated_shop" in st.session_state:
            if st.button("🛒 Add to Cart"):
                st.session_state.cart["shop"] = st.session_state.cart.get("shop", [])  
                st.session_state.cart["shop"].append(st.session_state.generated_shop)  
                save_cart()
                st.success("Added to Cart!")


    ### Chapter Adaptation
    elif st.session_state.page == "Adapt Chapter":
        st.subheader("📖 Adapt Chapter to Campaign")
        st.write("Modify your campaign text dynamically.")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            original_chapter = st.text_area("Original Chapter", height=500)
            if st.button("Load"):
                # Load functionality would go here
                pass
        
        with col2:
            edits_input = st.text_area("Edits Input", height=500)
            if st.button("What do you think?"):
                # Feedback functionality would go here
                pass
        
        with col3:
            ai_output = st.text_area("AI Output", height=500)
    

    ### Campaign AI Asst.
    elif st.session_state.page == "Campaign Assistant":
        st.subheader("🧠 Campaign Assistant")
        st.write("Ask me anything !")
        st.text_input("Enter your query:")
        st.button("Submit Query")


    ### Encounter generator
    elif st.session_state.page == "Encounter Generator":
        st.subheader("⚔️ Encounter Generator")
        st.write("Generate encounters based on party size and details.")
        st.number_input("Party Size", min_value=1, step=1, max_value=20)
        st.number_input("Party Level", min_value=1, step=1, max_value=20)
        st.text_input("Custom Encounter Prompt:")
        st.button("Generate Encounter")

    ### Dungeon Gen. 
    elif st.session_state.page == "Dungeon Generator":
        st.subheader("🏰 Dungeon Generator")
        st.write("Enter dungeon details and generate a full layout.")
        dungeon_prompt = st.text_area("Dungeon Prompt:")
        st.button("Generate Dungeon")
      
        if st.button("Generate Dungeon"):
            # Placeholder logic for dungeon generation
            st.session_state.generated_dungeon = "A mysterious dungeon layout appears..."
            st.text_area("Generated Dungeon:", st.session_state.generated_dungeon, height=250)
          
        if "generated_dungeon" in st.session_state:
            if st.button("🗺️ Generate Grid Battle Map"):
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


    ### Quest Gen.
    elif st.session_state.page == "Quest Generator":
        st.subheader("📜 Quest Generator")
        st.write("Generate a quest based on input details.")
        st.text_input("Quest Prompt:")
        st.button("Generate Quest")

    ### Worldbuilding Gen.
    elif st.session_state.page == "Worldbuilding":
        st.subheader("🌍 Worldbuilding Expansion")
        st.write("Auto-fill lore and expand world details.")
        st.button("Generate World Lore")

    ### Session Management
    elif st.session_state.page == "Session Management":
        st.subheader("🗒 Session Management")
        st.write("Tools for session intros and note assistance.")
        st.text_input("Session Details (e.g., S01):")
        st.button("Load Session History")

    except Exception as e:
        st.error(f"An error occurred: {e}")
        logging.error(f"Error in main application logic: {e}")

if __name__ == "__main__":
    main()


add_to_cart("NPCs", "add_npc_to_cart", "generated_npc")
add_to_cart("Shops", "add_shop_to_cart", "generated_shop")
add_to_cart("Locations", "add_location_to_cart", "generated_location")


import streamlit as st
import obsidian  # Ensure full module import for debugging
from obsidian import list_drive_files, upload_file, download_file
import ssl
import time
import os
import re
import json
import logging
import yaml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Import AI and Obsidian functionalities
from ai import (
    generate_npc,
    generate_shop,
    generate_location,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load Configuration from YAML
class Settings(BaseSettings):
    def __init__(self, config_file='config.yaml'):
        with open(config_file) as f:
            config = yaml.safe_load(f)
        super().__init__(**config)

settings = Settings()

# Load environment variables
load_dotenv()

# Centralized session management
class SessionState:
    def __init__(self):
        self.api_key = None
        self.cart = {}
        self.page = "API Key"

session_state = SessionState()

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
    """Initialize session state variables only once."""
    if "initialized" not in st.session_state:
        st.session_state.api_key = None
        st.session_state.cart = {}
        st.session_state.page = "API Key"
        st.session_state.selected_content_to_save = None
        st.session_state.selected_category = ""
        st.session_state.selected_file = ""
        st.session_state.initialized = True  # Mark as initialized

initialize_session_state()

@handle_exception
def save_cart():
    """Save the current cart to a structured local file."""
    default_cart_structure = {
        "NPCs": [],
        "Shops": [],
        "Locations": [],
        "Encounters": [],
        "Dungeons": [],
        "Quests": []
    }

    # Merge with existing session cart (preserving generated items)
    st.session_state.cart = {**default_cart_structure, **st.session_state.cart}

    with open("cart.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.cart, f, indent=4)
    
    st.success("✅ Cart saved with structured format!")

@handle_exception
def save_to_vault(category, item):
    """Save generated content to the cart under a specific category."""
    st.session_state.cart[category] = st.session_state.cart.get(category, [])
    st.session_state.cart[category].append(item)
    save_cart()
    st.success(f"Added to {category} in the cart!")

@handle_exception
def load_cart():
    """Load the cart from a local file if it exists, ensuring structure."""
    file_path = "cart.json"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        # Ensure all expected categories exist
        default_cart_structure = {
            "NPCs": [],
            "Shops": [],
            "Locations": [],
            "Encounters": [],
            "Dungeons": [],
            "Quests": []
        }
        st.session_state.cart = {**default_cart_structure, **loaded_data}

        st.success("✅ Cart loaded with structured format!")
    else:
        st.warning("No saved cart found locally.")

# Ensure saving to vault happens only when a button is pressed
if st.session_state.get("selected_content_to_save"):
    if st.button("📁 Save to Vault", key="save_to_vault"):
        base_filename = f"{st.session_state['selected_category']}_{st.session_state['selected_file']}"[:50]
        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', base_filename) + ".md"
        save_to_vault(st.session_state["selected_category"], st.session_state["selected_content_to_save"])
        st.session_state["selected_content_to_save"] = None  # Clear after saving

def add_to_cart(category, session_key):
    """Save generated content to the cart under a specific category (JSON only)."""
    if session_key in st.session_state:
        if st.button(f"🛒 Add to Cart", key=f"add_{session_key}_to_cart"):
            st.session_state.cart[category] = st.session_state.cart.get(category, [])
            st.session_state.cart[category].append(st.session_state[session_key])
            save_cart()
            st.success(f"✅ {session_key} added to {category} in the cart!")

def navigate_to(page_name):
    """Change the current page in the session state."""
    st.session_state.page = page_name

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
    st.title("Enter your API Key")
    session_state.api_key = st.text_input("API Key", type="password")
    if st.button("Submit", key="submit_api_key"):
        if session_state.api_key:
            st.success("API Key set!")
            session_state.page = "Main Menu"
        else:
            st.error("Please enter a valid API Key.")

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


def render_worldbuilding_page
    st.title("🌍 Worldbuilding Expansion & Lore)
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
          
    if "generated_dungeon" in st.session_state:
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
    st.write("Ask me anything !")
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
         shop = generate_shop(st.session_state.api_key, shop_type, shop_prompt)  
         st.session_state.generated_shop = shop  
         st.text_area(f"Generated {shop_type}:", shop, height=250)

    if "generated_shop" in st.session_state:
        add_to_cart("Shops", "generated_shop")

  
def render_create_location_page():
    st.title("📍 Create Location")
    render_sidebar()
    location_prompt = st.text_area("What do you already know about this location? (Optional)")
    if st.button("Generate Location", key="generate_location_button"):
        location = generate_location(st.session_state.api_key, location_prompt)  
        st.session_state.generated_location = location  
        st.text_area("Generated Location:", location, height=250)

    if "generated_location" in st.session_state:
        add_to_cart("Locations", "generated_location")
        st.success("Added to Cart!")
  
def render_generate_npc_page():
    st.title("🧙 Generate NPC")
    render_sidebar()
    npc_prompt = st.text_area("What do you already know about this NPC? (Optional)")
        
    if st.button("Generate NPC", key="generate_npc_button"):
        npc = generate_npc(st.session_state.api_key, npc_prompt)  
        st.session_state.generated_npc = npc  
        st.text_area("Generated NPC:", npc, height=250)  
      
   if "generated_npc" in st.session_state:
       add_to_cart("NPCs", "generated_npc")  # ✅ This replaces the redundant button logic

  
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
    "Generate NPC": render_generate_npc_page
    "Worldbuilding and Lore": render_worldbuilding_page
}

def render_page():
    """Dynamically render the selected page."""
    page_function = PAGES.get(session_state.page, lambda: st.error("Page not found."))
    page_function()

if __name__ == "__main__":
    render_page()



import streamlit as st
import obsidian  # Ensure full module import for debugging
from obsidian import list_drive_files, upload_file, download_file
import ssl
import time
import os
import re
import json
import logging
import yaml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

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
    """Initialize session state variables only once."""
    if not hasattr(st.session_state, "initialized"):
        # Define all session state variables in one place to avoid redundant checks
        session_defaults = {
            "api_key": None,
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
    """Load the cart from a local file if it exists, ensuring structure."""
    file_path = "cart.json"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        st.session_state.cart = {**DEFAULT_CART_STRUCTURE, **loaded_data}
        st.success("✅ Cart loaded with structured format!")
    else:
        st.warning("No saved cart found locally.")

if not hasattr(st.session_state, "selected_content_to_save"):
    st.session_state.selected_content_to_save = None

if not hasattr(st.session_state, "page"):
    st.session_state.page = "API Key"  # Ensure default page is set

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
    if hasattr(st.session_state, session_key):
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
    """Change the current page in Streamlit session state."""
    st.session_state.page = page_name  # ✅ Corrected

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
    load_cart()
    st.title("Enter your API Key")
    st.session_state.api_key = st.text_input("API Key", type="password")  # ✅ Corrected
    if st.button("Submit", key="submit_api_key"):
        if st.session_state.api_key:  # ✅ Corrected state usage
            st.success("API Key set!")
            st.session_state.page = "Main Menu"  # ✅ Now Streamlit recognizes the change
        else:
            st.error("Please enter a valid API Key.")

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
          
    if st.session_state.generated_dungeon:
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
    if st.session_state.generated_encounter:

  
def render_campaign_assistant_page():
    st.title("📖 Campaign Assistant")
    render_sidebar()
    st.write("Ask me anything !")
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
         shop = generate_shop(st.session_state.api_key, shop_type, shop_prompt)  
         st.session_state.generated_shop = shop  
         st.text_area(f"Generated {shop_type}:", shop, height=250)

    if st.session_state.generated_shop:
        add_to_cart("Shops", "generated_shop")

def render_create_location_page():
    st.title("📍 Create Location")
    render_sidebar()
    location_prompt = st.text_area("What do you already know about this location? (Optional)")
    if st.button("Generate Location", key="generate_location_button"):
        location = generate_location(st.session_state.api_key, location_prompt)  
        st.session_state.generated_location = location  
        st.text_area("Generated Location:", location, height=250)

    if st.session_state.generated_location:
        add_to_cart("Locations", "generated_location")
        st.success("Added to Cart!")

def render_generate_npc_page():
    st.title("🧙 Generate NPC")
    render_sidebar()
    npc_prompt = st.text_area("What do you already know about this NPC? (Optional)")
        
    if st.button("Generate NPC", key="generate_npc_button"):
        npc = generate_npc(st.session_state.api_key, npc_prompt)  
        st.session_state.generated_npc = npc  
        st.text_area("Generated NPC:", npc, height=250)  
      
    if st.session_state.generated_npc:
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
    """Dynamically render the selected page."""
    page_function = PAGES.get(st.session_state.page, lambda: st.error("Page not found."))
    page_function()

if __name__ == "__main__":
    render_page()



---

def render_embedding_page():
    st.title("📚 Embedding Management")
    st.write("Manage your campaign embeddings stored in ChromaDB.")
    render_sidebar()
    
    if st.button("🔄 Pull from GitHub Vault"):
        pull_github_vault()
    
    st.subheader("🔍 View Modified Files & Re-Embed")
    reembed_modified_files()

    st.subheader("🔍 View Stored Embeddings")
    embeddings = list_embeddings()
    if embeddings["ids"]:
        for i, (eid, doc) in enumerate(zip(embeddings["ids"], embeddings["documents"])):
            with st.expander(f"📄 {eid}"):
                st.write(doc)
                if st.button(f"❌ Remove {eid}", key=f"remove_{i}"):
                    remove_embedding(eid)
                    st.rerun()
    else:
        st.info("No embeddings stored yet.")
    
    st.subheader("➕ Add New Embedding")
    new_text = st.text_area("Enter text to embed:")
    metadata_input = st.text_input("Enter metadata (optional, JSON format):", "{}")
    if st.button("Add Embedding"):
        try:
            metadata = json.loads(metadata_input)
            if not isinstance(metadata, dict):
                metadata = {"source": "manual"}  # Ensure metadata is a dictionary
            add_embedding(new_text, metadata)
            st.rerun()
        except json.JSONDecodeError:
            st.error("Invalid metadata JSON format.")
    
    st.subheader("🧠 Campaign Assistant")
    user_query = st.text_input("Ask something about your campaign:")
    if st.button("Get AI Answer"):
        if "openai_api_key" in st.session_state and st.session_state.openai_api_key:
            response = generate_ai_response(user_query, st.session_state.openai_api_key)
            st.markdown("### 🤖 AI Response")
            st.write(response)
        else:
            st.error("⚠️ Please enter your OpenAI API key in settings.")


