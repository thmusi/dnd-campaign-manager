import streamlit as st
from streamlit_extras.switch_page_button import switch_page
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

# Function to check API Key and proceed
def check_api_key():
    api_key = st.session_state.get("api_key", "")
    if api_key:
        switch_page("Main Menu")
    else:
        st.warning("Please enter a valid API Key to continue.")

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
        st.session_state.npc_input = st.text_area("Describe the NPC or leave blank for AI generation:")
        if st.button("Generate NPC"):
            if "api_key" in st.session_state and st.session_state.api_key:
                response = generate_npc(st.session_state.npc_input, st.session_state.api_key)
                st.session_state.generated_npc = response
            else:
                st.warning("Please enter a valid API Key to generate content.")
        if "generated_npc" in st.session_state:
            st.text_area("Generated NPC:", value=st.session_state.generated_npc, height=200)
    
    if st.button("🏪 Create Shop"):
        st.session_state.shop_input = st.text_area("Describe the shop or leave blank for AI generation:")
        if st.button("Generate Shop"):
            if "api_key" in st.session_state and st.session_state.api_key:
                response = generate_shop(st.session_state.shop_input, st.session_state.api_key)
                st.session_state.generated_shop = response
            else:
                st.warning("Please enter a valid API Key to generate content.")
        if "generated_shop" in st.session_state:
            st.text_area("Generated Shop:", value=st.session_state.generated_shop, height=200)
    
    if st.button("📍 Create Location"):
        st.session_state.location_input = st.text_area("Describe the location or leave blank for AI generation:")
        if st.button("Generate Location"):
            if "api_key" in st.session_state and st.session_state.api_key:
                response = generate_location(st.session_state.location_input, st.session_state.api_key)
                st.session_state.generated_location = response
            else:
                st.warning("Please enter a valid API Key to generate content.")
        if "generated_location" in st.session_state:
            st.text_area("Generated Location:", value=st.session_state.generated_location, height=200)
    
    if st.button("📖 Adapt Chapter to Campaign"):
        switch_page("Adapt Chapter")
    if st.button("🧠 Campaign Assistant (AI-Powered Q&A)"):
        switch_page("Campaign Assistant")
    if st.button("⚔️ Encounter Generator"):
        switch_page("Encounter Generator")
    if st.button("🏰 Dungeon Generator"):
        switch_page("Dungeon Generator")
    if st.button("📜 Quest Generator"):
        switch_page("Quest Generator")
    if st.button("🌍 Worldbuilding Expansion & Auto-Filled Lore"):
        switch_page("Worldbuilding")
    if st.button("🗒 Session Management"):
        switch_page("Session Management")
    
    # Cart actions
    if st.sidebar.button("Save Cart"):
        save_cart()
    if st.sidebar.button("Load Cart"):
        load_cart()

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
