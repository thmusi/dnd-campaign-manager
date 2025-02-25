import os
import json
import dropbox
import streamlit as st
from dropbox.files import WriteMode
from dotenv import load_dotenv
import logging

# Import AI and Obsidian functionalities
from ai import (
    generate_npc,
    generate_shop,
    generate_location,
    modify_campaign_chapter,
    ai_search_campaign_notes,
)
from obsidian import (
    test_dropbox_upload,
    write_note,
    list_campaign_files,
    fetch_note_content,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

if not DROPBOX_ACCESS_TOKEN:
    st.error("❌ Dropbox API Key is missing! Please check your environment variables.")
    st.stop()  # Stop execution if the API key is missing

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

CART_FILE = "/Apps/DnDManager/cart.json"

# Initialize session state
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "page" not in st.session_state:
    st.session_state.page = "API Key"

def save_cart():
    """Save the current cart to Dropbox."""
    try:
        json_data = json.dumps(st.session_state.cart)
        dbx.files_upload(json_data.encode(), CART_FILE, mode=WriteMode("overwrite"))
        st.success("Cart saved!")
        logging.info("Cart saved successfully.")
    except Exception as e:
        st.error(f"Failed to save cart: {e}")
        logging.error(f"Error saving cart: {e}")

def load_cart():
    """Load the cart from Dropbox."""
    try:
        _, res = dbx.files_download(CART_FILE)
        st.session_state.cart = json.loads(res.content)
        st.success("Cart loaded!")
    except dropbox.exceptions.HttpError:
        st.warning("No saved cart found.")
    except Exception as e:
        st.error(f"Error loading cart: {e}")

def save_to_vault(content, filename="generated_content.md"):
    """Saves the modified content to the user's Obsidian-Dropbox vault."""
    vault_path = f"/Obsidian-Vault/{filename}"
    try:
        dbx.files_upload(content.encode("utf-8"), vault_path, mode=WriteMode("overwrite"))
        st.success(f"File saved successfully to {vault_path}")
    except Exception as e:
        st.error(f"Error saving to vault: {e}")

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
                                save_to_vault(edited_content, filename=f"{selected_category}_{selected_file}.md")
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
                st.text_area("Original Chapter", height=500)
                st.button("Load")
            with col2:
                st.text_area("Edits Input", height=500)
            with col3:
                st.text_area("AI Output", height=500)
                st.button("Refresh")


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
        st.number_input("Party Size", min_value=1, step=1)
        st.text_input("Custom Encounter Prompt:")
        st.button("Generate Encounter")

    ### Dungeon Gen. 
    elif st.session_state.page == "Dungeon Generator":
        st.subheader("🏰 Dungeon Generator")
        st.write("Enter dungeon details and generate a full layout.")
        st.text_input("Dungeon Prompt:")
        st.button("Generate Dungeon")

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

if __name__ == "__main__":
    main()
