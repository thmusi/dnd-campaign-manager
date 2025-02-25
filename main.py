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
else:
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
        if st.session_state.page not in "Main Menu":
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
            npc = generate_npc(st.session_state.api_key, npc_prompt)  # Fix: Use the correct variable
            st.session_state.generated_npc = npc  # Store generated NPC
            st.markdown("### 🛡️ PNJ Généré")
            st.markdown(npc)

        if "generated_npc" in st.session_state:  # Fix: Check for the correct key
            with st.expander("🛡️ View & Edit NPC"):
                st.session_state.generated_npc = st.text_area("Modify NPC", value=st.session_state.generated_npc, height=250)
            if st.button("🛒 Add to Cart"):
                st.session_state.cart["npc"] = st.session_state.cart.get("npc", [])  # Fix: Ensure the list exists
                st.session_state.cart["npc"].append(st.session_state.generated_npc)
                save_cart()
                st.success("Added to Cart!")

    # Cart page rendering
    elif st.session_state.page == "Cart":
        st.title("🛒 Your Cart")
        categories = list(st.session_state.cart.keys())
        selected_category = st.selectbox("📂 Select Folder", categories)
        files = st.session_state.cart[selected_category]
        selected_file = st.selectbox(f"📜 Files in {selected_category}", files)
        if selected_file:
            st.markdown("### 📖 Preview")
            st.markdown(selected_file)

if __name__ == "__main__":
    main()
