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
if not DROPBOX_ACCESS_TOKEN:
    st.error("❌ Dropbox API Key is missing! Please check your environment variables.")
else:
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
CART_FILE = "/Apps/DnDManager/cart.json"

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'cart' not in st.session_state:
    st.session_state.cart = {}

# Function to save and load cart

def save_cart():
    json_data = json.dumps(st.session_state.cart)
    dbx.files_upload(json_data.encode(), CART_FILE, mode=WriteMode("overwrite"))
    st.success("Cart saved!")

def load_cart():
    try:
        _, res = dbx.files_download(CART_FILE)
        st.session_state.cart = json.loads(res.content.decode("utf-8"))
    except dropbox.exceptions.AuthError:
        st.error("❌ Dropbox authentication failed! Check your access token.")
    except dropbox.exceptions.ApiError:
        st.warning("No saved cart found.")

if 'cart_loaded' not in st.session_state:
    load_cart()
    st.session_state.cart_loaded = True

# First Page: API Key Input
if st.session_state.api_key is None or st.session_state.api_key == "":
    st.title("🔑 Enter Your OpenAI API Key")
    st.write("Please enter your OpenAI API Key to proceed.")
    api_key_input = st.text_input("API Key", type="password")
    if st.button("Save API Key"):
        st.session_state.api_key = api_key_input
        os.environ["DROPBOX_ACCESS_TOKEN"] = api_key_input  # Persist API key
        st.success("API Key Saved! Reloading...")
        st.rerun()
    st.stop()

# Top Dropdown Navigation Menu
menu_options = {
    "Characters & Shops": ["Create NPC", "Create Shop"],
    "Story & Campaign Tools": ["Adapt Chapter to Campaign", "Campaign Assistant"],
    "Encounters & Dungeons": ["Encounter Generator", "Dungeon Generator"],
    "Quests & Worldbuilding": ["Quest Generator", "Worldbuilding Expansion"],
    "Session Management": ["Session Work Tools"],
    "Cart": ["View Cart"],
    "Settings": ["API Key Input", "Theme Customization"]
}


selected_tool = st.sidebar.radio("🛠 Select Page", sum(menu_options.values(), []))


# Page Routing
if selected_tool == "🧙 Create NPC":
    st.header("🧑‍🎤 NPC Generator")
    npc_input = st.text_area("Describe your NPC (optional)")
    if st.button("Generate NPC"):
        npc_result = generate_npc(st.session_state.api_key, npc_input)
        st.write(npc_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("NPCs", []).append(npc_result)
        if st.button("Send to Quest Generator"):
            st.session_state.cart.setdefault("Quests", []).append(npc_result)

elif selected_tool == "🏪 Create Shop":
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
elif selected_tool == "Quests":
    st.header("📜 Quest Generator")
    quest_prompt = st.text_area("Describe your quest")
    if st.button("Generate Quest"):
        quest_result = "(AI Quest Result Here)"  # Placeholder for AI quest generation function
        st.write(quest_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("Quests", []).append(quest_result)

elif selected_tool == "Encounters":
    st.header("⚔️ Encounter Generator")
    encounter_input = st.text_area("Describe your encounter (optional)")
    if st.button("Generate Encounter"):
        encounter_result = "(AI-generated encounter content here)"
        st.write(encounter_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("Encounters", []).append(encounter_result)
        if st.button("Create Quest from Encounter"):
            st.session_state.cart.setdefault("Quests", []).append(encounter_result)

elif selected_tool == "🏰 Dungeon Generator":
    st.header("🏰 Dungeon Generator")
    dungeon_input = st.text_area("Describe your dungeon (optional)")
    if st.button("Generate Dungeon"):
        dungeon_result = "(AI-generated dungeon content here)"
        st.write(dungeon_result)
        if st.button("Save to Cart"):
            st.session_state.cart.setdefault("Dungeons", []).append(dungeon_result)

elif selected_tool == "Worldbuilding":
    st.header("🌍 Worldbuilding Expansion")
    st.write("Generate factions, cultures, and auto-filled lore.")

elif selected_tool == "Session Management":
    st.header("📝 Session Work Tools")
    st.write("Assist with session logs, summaries, and planning.")

elif selected_tool == "Settings":
    st.header("⚙️ Settings")

# Collapsible AI Assistant Panel
with st.expander("🧠 Campaign AI Assistant"):
    assistant_query = st.text_input("Ask the AI about your campaign")
    if assistant_query:
        ai_response = "(AI Response Here)"  # Placeholder for AI function
        st.write(ai_response)



if selected_tool == "🛒 View Cart":
    st.header("🛒 Your Cart")
    if st.button("Load Cart"):
        load_cart()
    categories = list(st.session_state.cart.keys())
    selected_category = st.selectbox("Choose a category", categories)
    if selected_category:
        for idx, item in enumerate(st.session_state.cart[selected_category]):
            with st.expander(f"📝 {selected_category.capitalize()} {idx+1}"):
                st.markdown(item)
                if st.button(f"Generate Related Content from {selected_category.capitalize()} {idx+1}", key=f"generate_{selected_category}_{idx}_{selected_tool}"):
                    if selected_category == "shop":
                        st.session_state.generated_content = generate_npc(st.session_state.api_key, item)
                        st.success("NPC Generated from Shop Details!")
    if st.button("Save Cart"):
        save_cart()

st.sidebar.button("💾 Save Cart to Dropbox", on_click=save_cart, key="save_cart_button")

