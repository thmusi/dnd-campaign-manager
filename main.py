import streamlit as st
import obsidian  # Ensure full module import for debugging
from obsidian import list_drive_files, upload_file, download_file
import ssl
import time
import os
import re
import json
import logging
from dotenv import load_dotenv
from pydantic import BaseSettings

# Import AI and Obsidian functionalities
from ai import (
    generate_npc,
    generate_shop,
    generate_location,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configuration Management
class Settings(BaseSettings):
    GOOGLE_DRIVE_API_CREDENTIALS: str = "{}"

settings = Settings()

# Load environment variables
load_dotenv()

def handle_exception(func):
    """Centralized error handling decorator."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"An error occurred: {e}")
            logging.error(f"Error in {func.__name__}: {e}")
            return None
    return wrapper

@handle_exception
def initialize_session_state():
    """Initialize session state variables."""
    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    if "cart" not in st.session_state:
        st.session_state.cart = {}
    if "page" not in st.session_state:
        st.session_state.page = "API Key"
    if "selected_content_to_save" not in st.session_state:
        st.session_state.selected_content_to_save = None
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = ""
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = ""

initialize_session_state()

@handle_exception
def save_cart():
    """Save the current cart to Google Drive."""
    json_data = json.dumps(st.session_state.cart)
    file_path = "cart.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json_data)
    upload_file(file_path)
    st.success("Cart saved to Google Drive!")
    logging.info("Cart saved successfully to Google Drive.")

@handle_exception
def download_cart_file(file_id):
    """Download the cart.json file from Google Drive."""
    attempts = 3
    for attempt in range(attempts):
        try:
            download_file(file_id, "cart.json")
            return True
        except ssl.SSLError:
            st.warning(f"SSL error, retrying... ({attempt+1}/{attempts})")
            logging.warning(f"SSL error on attempt {attempt+1}")
            time.sleep(2)
    return False

@handle_exception
def validate_cart_file():
    """Validate the downloaded cart.json file."""
    if not os.path.exists("cart.json"):
        st.error("Downloaded cart.json is missing.")
        return False
    if os.stat("cart.json").st_size == 0:
        st.error("Downloaded cart.json is empty. Try saving the cart again.")
        return False
    return True

@handle_exception
def load_cart():
    """Load the cart from Google Drive with validation and retries."""
    files = list_drive_files()
    file_id = next((file["id"] for file in files if file["name"] == "cart.json"), None)
    if not file_id:
        st.warning("No saved cart found in Google Drive.")
        return
    if download_cart_file(file_id) and validate_cart_file():
        with open("cart.json", "r", encoding="utf-8") as f:
            st.session_state.cart = json.load(f)
        st.success("Cart loaded from Google Drive!")

@handle_exception
def save_to_vault(content, filename="generated_content.md"):
    """Saves content to the user's Obsidian-Google Drive vault."""
    vault_path = "obsidian_vault"
    os.makedirs(vault_path, exist_ok=True)
    if not filename.endswith(".md"):
        filename += ".md"
    file_path = os.path.join(vault_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    upload_file(file_path)
    st.success(f"✅ File saved successfully to Google Drive: {filename}")

# Ensure saving to vault happens only when a button is pressed
if st.session_state.get("selected_content_to_save"):
    if st.button("📁 Save to Vault", key="save_to_vault"):
        base_filename = f"{st.session_state['selected_category']}_{st.session_state['selected_file']}"[:50]
        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', base_filename) + ".md"
        save_to_vault(st.session_state["selected_content_to_save"], filename=safe_filename)
        st.session_state["selected_content_to_save"] = None  # Clear after saving

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

def main():
    """Main function to run the Streamlit application."""
    render_sidebar()
    load_cart()
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
        if st.button("Generate NPC", key="generate_npc_button"):
            npc = generate_npc(st.session_state.api_key, npc_prompt)  
            st.session_state.generated_npc = npc  
            st.text_area("Generated NPC:", npc, height=250)  

        if "generated_npc" in st.session_state:
            if st.button("🛒 Add to Cart", key="add_npc_to_cart"):
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
                        if st.button("Send to Vault", key="send_to_vault"):
                            if edited_content.strip():
                                # Trim filename to avoid excessively long names
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
        if st.button("Generate Location", key="generate_location_button"):
            location = generate_location(st.session_state.api_key, location_prompt)  
            st.session_state.generated_location = location  
            st.text_area("Generated Location:", location, height=250)

        if "generated_location" in st.session_state:
            if st.button("🛒 Add to Cart", key="add_location_to_cart"):
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
        if st.button("Generate Shop", key="generate_shop_button"):
            shop = generate_shop(st.session_state.api_key, shop_type, shop_prompt)  
            st.session_state.generated_shop = shop  
            st.text_area(f"Generated {shop_type}:", shop, height=250)

        if "generated_shop" in st.session_state:
            if st.button("🛒 Add to Cart", key="add_shop_to_cart"):
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
    

    ### Campaign AI Asst.
    elif st.session_state.page == "Campaign Assistant":
        st.subheader("🧠 Campaign Assistant")
        st.write("Ask me anything !")
        st.text_input("Enter your query:", key="query_input")
        st.button("Submit Query", key="submit_query")

    ### Encounter generator
    elif st.session_state.page == "Encounter Generator":
        st.subheader("⚔️ Encounter Generator")
        st.write("Generate encounters based on party size and details.")
        st.number_input("Party Size", min_value=1, step=1, max_value=20, key="party_size_input")
        st.number_input("Party Level", min_value=1, step=1, max_value=20, key="party_level_input")
        st.text_input("Custom Encounter Prompt:", key="custom_encounter_input")
        st.button("Generate Encounter", key="generate_encounter_button")

    ### Dungeon Gen. 
    elif st.session_state.page == "Dungeon Generator":
        st.subheader("🏰 Dungeon Generator")
        st.write("Enter dungeon details and generate a full layout.")
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


    ### Quest Gen.
    elif st.session_state.page == "Quest Generator":
        st.subheader("📜 Quest Generator")
        st.write("Generate a quest based on input details.")
        st.text_input("Quest Prompt:", key="quest_prompt_input")
        st.button("Generate Quest", key="generate_quest_button")

    ### Worldbuilding Gen.
    elif st.session_state.page == "Worldbuilding":
        st.subheader("🌍 Worldbuilding Expansion")
        st.write("Auto-fill lore and expand world details.")
        st.button("Generate World Lore", key="generate_world_lore_button")

    ### Session Management
    elif st.session_state.page == "Session Management":
        st.subheader("🗒 Session Management")
        st.write("Tools for session intros and note assistance.")
        st.text_input("Session Details (e.g., S01):", key="session_details_input")
        st.button("Load Session History", key="load_session_history_button")

if __name__ == "__main__":
    main()
