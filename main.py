import streamlit as st
import openai  # Ensure OpenAI API is properly integrated
import os
import json
import dropbox
from dropbox.files import WriteMode
from dotenv import load_dotenv

# Import AI and Obsidian functionalities
from ai import generate_npc, generate_shop, generate_location, modify_campaign_chapter, ai_search_campaign_notes
from obsidian import test_dropbox_upload, write_note, list_campaign_files, fetch_note_content

# Load environment variables
load_dotenv()
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
if not DROPBOX_ACCESS_TOKEN:
    st.error("❌ Dropbox API Key is missing! Please check your environment variables.")
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

# Function to save and load cart
def save_cart():
    json_data = json.dumps(st.session_state.cart)
    dbx.files_upload(json_data.encode(), CART_FILE, mode=WriteMode("overwrite"))
    st.success("Cart saved!")

def load_cart():
    try:
        _, res = dbx.files_download(CART_FILE)
        st.session_state.cart = json.loads(res.content)
        st.success("Cart loaded!")
    except Exception as e:
        st.warning("No saved cart found.")

# Function to change pages
def navigate_to(page_name):
    st.session_state.page = page_name

# Sidebar Navigation (visible on all pages except API Key and Landing Page)
def render_sidebar():
    if st.session_state.page not in ["API Key"]:
        with st.sidebar:
            st.title("Navigation")
            if st.button("🏠 Home"):
                navigate_to("Main Menu")
            if st.button("🛒 Cart"):
                navigate_to("Cart")
            st.markdown("---")
    if st.session_state.page not in ["API Key", "Main Menu"]:
        with st.sidebar:
            st.title("Navigation")
            if st.button("🏠 Home"):
                navigate_to("Main Menu")
            if st.button("🛒 Cart"):
                navigate_to("Cart")
            st.markdown("---")
            if st.button("🧙 Create NPC"):
                navigate_to("Generate NPC")
            if st.button("🏪 Create Shop"):
                navigate_to("Create Shop")
            if st.button("📍 Create Location"):
                navigate_to("Create Location")
            if st.button("📖 Adapt Chapter to Campaign"):
                navigate_to("Adapt Chapter")
            if st.button("🧠 Campaign Assistant"):
                navigate_to("Campaign Assistant")
            if st.button("⚔️ Encounter Generator"):
                navigate_to("Encounter Generator")
            if st.button("🏰 Dungeon Generator"):
                navigate_to("Dungeon Generator")
            if st.button("📜 Quest Generator"):
                navigate_to("Quest Generator")
            if st.button("🌍 Worldbuilding"):
                navigate_to("Worldbuilding")
            if st.button("🗒 Session Management"):
                navigate_to("Session Management")

# 1st Page: API Key Input
if "api_key" not in st.session_state:
    st.title("D&D AI Campaign Manager")
    st.text_input("Enter your OpenAI API Key:", type="password", key="api_key")
    st.button("Submit", on_click=check_api_key)
else:
    # 2nd Page: Main Menu
    st.title("Main Menu")
    st.sidebar.title("Navigation")
    
    # Main navigation buttons
    if st.button("🧙 Create NPC"):
        navigate_to("Generate NPC")
    if st.button("🏪 Create Shop"):
        navigate_to("Generate Shop")
    if st.button("📍 Create Location"):
        navigate_to("Generate Location")
    if st.button("📖 Adapt Chapter to Campaign"):
        navigate_to("Adapt Chapter")
    if st.button("🧠 Campaign Assistant (AI-Powered Q&A)"):
        navigate_to("Campaign Assistant")
    if st.button("⚔️ Encounter Generator"):
        navigate_to("Encounter Generator")
    if st.button("🏰 Dungeon Generator"):
        navigate_to("Dungeon Generator")
    if st.button("📜 Quest Generator"):
        navigate_to("Quest Generator")
    if st.button("🌍 Worldbuilding Expansion & Auto-Filled Lore"):
        navigate_to("Worldbuilding")
    if st.button("🗒 Session Management"):
        navigate_to("Session Management")


# Keep styling similar to landing.css using Streamlit's built-in styles
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

