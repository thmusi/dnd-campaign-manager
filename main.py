import streamlit as st
import openai
import json
import dropbox
import os
from dropbox.files import WriteMode
from dotenv import load_dotenv
from ai import generate_npc, generate_shop, generate_location, modify_campaign_chapter
from obsidian import test_dropbox_upload, write_note, list_campaign_files, fetch_note_content
from ai import ai_search_campaign_notes

# Load environment variables
load_dotenv()
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
CART_FILE = "/Apps/DnDManager/cart.json"

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Initialize session state for API key and cart if not set
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'cart' not in st.session_state:
    st.session_state.cart = {}

# UI Styling and Top Bar Navigation
st.markdown("""
    <style>
    .top-bar {
        background-color: #2E2E2E;
        padding: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
    }
    .dropdown {
        padding: 8px;
        background-color: #3E3E3E;
        border-radius: 5px;
        color: white;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("🧙 D&D Campaign Manager")
page = st.sidebar.radio("Navigation", ["Home", "Create NPC", "Create Shop", "Quests", "Encounters", "Dungeon Generator", "Worldbuilding", "Session Management", "Settings"])

# Search Bar
search_query = st.text_input("🔍 Quick Search (Spells, NPCs, etc.)")
if search_query:
    search_results = ai_search_campaign_notes(search_query)
    st.write("### Search Results")
    for result in search_results:
        st.write(result)

# Page Routing
if page == "Home":
    st.title("🏰 Welcome to Your D&D Campaign Manager")
    st.write("Manage your world, generate content, and plan your sessions seamlessly.")

elif page == "Create NPC":
    st.header("🧑‍🎤 NPC Generator")
    npc_input = st.text_area("Describe your NPC (optional)")
    if st.button("Generate NPC"):
        npc_result = generate_npc(st.session_state.api_key, npc_input)
        st.write(npc_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("NPCs", []).append(npc_result)

elif page == "Create Shop":
    st.header("🏪 Shop Generator")
    shop_type = st.selectbox("Select Shop Type", ["General Store", "Blacksmith", "Magic Shop", "Tavern"])
    shop_input = st.text_area("Describe your shop (optional)")
    if st.button("Generate Shop"):
        shop_result = generate_shop(st.session_state.api_key, shop_type, shop_input)
        st.write(shop_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("Shops", []).append(shop_result)

elif page == "Quests":
    st.header("📜 Quest Generator")
    quest_prompt = st.text_area("Describe your quest")
    if st.button("Generate Quest"):
        quest_result = "(AI Quest Result Here)"  # Placeholder for AI quest generation function
        st.write(quest_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("Quests", []).append(quest_result)

elif page == "Encounters":
    st.header("⚔️ Encounter Generator")
    encounter_prompt = st.text_area("Describe encounter details")
    if st.button("Generate Encounter"):
        encounter_result = "(AI Encounter Result Here)"  # Placeholder for AI function
        st.write(encounter_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("Encounters", []).append(encounter_result)

elif page == "Dungeon Generator":
    st.header("🏰 Dungeon Generator")
    dungeon_prompt = st.text_area("Describe your dungeon")
    if st.button("Generate Dungeon"):
        dungeon_result = "(AI Dungeon Result Here)"  # Placeholder for AI function
        st.write(dungeon_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("Dungeons", []).append(dungeon_result)

elif page == "Worldbuilding":
    st.header("🌍 Worldbuilding Expansion")
    st.write("Generate factions, cultures, and auto-filled lore.")

elif page == "Session Management":
    st.header("📝 Session Work Tools")
    st.write("Assist with session logs, summaries, and planning.")

elif page == "Settings":
    st.header("⚙️ Settings")
    api_key_input = st.text_input("Enter OpenAI API Key", type="password")
    if st.button("Save API Key"):
        st.session_state.api_key = api_key_input
        st.success("API Key Saved!")

# Collapsible AI Assistant Panel
with st.expander("🧠 Campaign AI Assistant"):
    assistant_query = st.text_input("Ask the AI about your campaign")
    if assistant_query:
        ai_response = "(AI Response Here)"  # Placeholder for AI function
        st.write(ai_response)

st.sidebar.button("💾 Save Cart to Dropbox", on_click=lambda: st.write("(Saving logic needed)"))
