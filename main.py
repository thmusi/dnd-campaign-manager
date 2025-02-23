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

# Popup for API Key Input
if st.session_state.api_key is None:
    st.markdown("""
        <style>
        .popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: #2E2E2E;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.5);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("<div class='popup'><h3>🔑 Enter Your OpenAI API Key</h3></div>", unsafe_allow_html=True)
    api_key_input = st.text_input("Enter OpenAI API Key", type="password")
    if st.button("Save API Key"):
        st.session_state.api_key = api_key_input
        st.success("API Key Saved!")
        st.experimental_rerun()

# UI Styling and Top Bar Navigation with Dropdown Categories
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

# Top Bar Navigation with Dropdown Categories
st.markdown("""
    <div class='top-bar'>
        <span>🏰 D&D Campaign Manager</span>
        <select id='dropdown' onchange='location = this.value;'>
            <option value='' selected disabled>📂 Select Category</option>
            <option value='npc'>🧑 Characters & Shops</option>
            <option value='story'>📜 Story & Campaign Tools</option>
            <option value='encounters'>⚔️ Encounters & Dungeons</option>
            <option value='quests'>🎭 Quests & Worldbuilding</option>
            <option value='session'>🗒 Session Management</option>
            <option value='settings'>⚙️ Settings & Customization</option>
        </select>
        <span>🔍 <input type='text' placeholder='Search campaign notes, NPCs, and quests'></span>
        <span>🛒 Cart</span>
    </div>
""", unsafe_allow_html=True)

# Dictionary for Category-Based Page Routing
categories = {
    "npc": ["🧙 Create NPC", "🏪 Create Shop"],
    "story": ["📖 Adapt Chapter to Campaign", "🧠 Campaign Assistant (AI-Powered Q&A)"],
    "encounters": ["🐉 Encounter Generator", "🏰 Dungeon Generator"],
    "quests": ["📜 Quest Generator", "🌍 Worldbuilding Expansion & Auto-Filled Lore"],
    "session": ["📝 Session Work Tools"],
    "settings": ["🔑 API Key Input", "🎨 Theme Customization"]
}

# Page Routing Based on Selected Tool
page = st.selectbox("Select Tool", sum(categories.values(), []))

if page == "🧙 Create NPC":
    st.header("🧑‍🎤 NPC Generator")
    npc_input = st.text_area("Describe your NPC (optional)")
    if st.button("Generate NPC"):
        npc_result = generate_npc(st.session_state.api_key, npc_input)
        st.write(npc_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("NPCs", []).append(npc_result)
        if st.button("Send to Quest Generator"):
            st.session_state.cart.setdefault("Quests", []).append(npc_result)

elif page == "🏪 Create Shop":
    st.header("🏪 Shop Generator")
    shop_type = st.selectbox("Select Shop Type", ["General Store", "Blacksmith", "Magic Shop", "Tavern"])
    shop_input = st.text_area("Describe your shop (optional)")
    if st.button("Generate Shop"):
        shop_result = generate_shop(st.session_state.api_key, shop_type, shop_input)
        st.write(shop_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("Shops", []).append(shop_result)
        if st.button("Generate NPC from Shop Owner"):
            st.session_state.cart.setdefault("NPCs", []).append(shop_result)

# Additional functionality for other tools follows the same pattern...
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
        if st.button("Create Quest from Encounter"):
            st.session_state.cart.setdefault("Quests", []).append(encounter_result)

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

# Collapsible AI Assistant Panel
with st.expander("🧠 Campaign AI Assistant"):
    assistant_query = st.text_input("Ask the AI about your campaign")
    if assistant_query:
        ai_response = "(AI Response Here)"  # Placeholder for AI function
        st.write(ai_response)

st.sidebar.button("💾 Save Cart to Dropbox", on_click=lambda: st.write("(Saving logic needed)"))
