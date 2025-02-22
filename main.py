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

load_dotenv()
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
CART_FILE = "/Apps/DnDManager/cart.json"

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

try:
    account_info = dbx.users_get_current_account()
    print(f"✅ Connected to Dropbox as {account_info.name.display_name}")
except dropbox.exceptions.AuthError:
    print("❌ Invalid Dropbox token! Check your credentials.")

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'cart' not in st.session_state:
    st.session_state.cart = {"npc": [], "shop": [], "location": [], "chapter": [], "campaign_assistant": [], "encounter": [], "dungeon": [], "quest": [], "worldbuilding": [], "session": []}

# Functions for saving/loading cart data
def save_cart():
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    json_data = json.dumps(st.session_state.cart)
    dbx.files_upload(json_data.encode(), CART_FILE, mode=WriteMode("overwrite"))
    st.success("Cart saved!")

def load_cart():
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    try:
        _, res = dbx.files_download(CART_FILE)
        st.session_state.cart = json.loads(res.content.decode("utf-8"))
    except dropbox.exceptions.AuthError:
        st.error("❌ Dropbox authentication failed! Check your access token.")
    except dropbox.exceptions.ApiError:
        st.warning("No saved cart found.")

def api_key_page():
    st.title("API Key Input")
    st.write("Please enter your OpenAI API Key to proceed.")
    api_key = st.text_input("OpenAI API Key", type="password")
    if st.button("Submit API Key"):
        if api_key:
            st.session_state.api_key = api_key
            st.success("API Key set successfully!")
            st.rerun()
        else:
            st.error("Please enter a valid API key.")

def main_menu():
    st.title("Main Menu")
    page = st.selectbox("📜 Select Section", ["Create NPC", "Create Shop", "Create Location", "Adapt Chapter to Campaign",
                                            "Campaign Assistant", "Encounter Generator", "Dungeon Generator",
                                            "Quest Generator", "Worldbuilding Expansion", "Session Work Tools", "🛒 Cart"])
    st.markdown("<div style='position: absolute; top: 10px; right: 20px;'>🛒 [Go to Cart](#)</div>", unsafe_allow_html=True)
    
    if page == "Create NPC":
        create_npc_page()
    elif page == "Create Shop":
        create_shop_page()
    elif page == "Create Location":
        create_location_page()
    elif page == "Adapt Chapter to Campaign":
        adapt_chapter_page()
    elif page == "Campaign Assistant":
        campaign_assistant_page()
    elif page == "Encounter Generator":
        encounter_generator_page()
    elif page == "Dungeon Generator":
        dungeon_generator_page()
    elif page == "Quest Generator":
        quest_generator_page()
    elif page == "Worldbuilding Expansion":
        worldbuilding_page()
    elif page == "Session Work Tools":
        session_work_tools_page()
    elif page == "🛒 Cart":
        cart_page()


def create_npc_page():
    st.header("🛡️ Generate an NPC")
    npc_prompt = st.text_area("What do you already know about this NPC? (Optional)")
    if st.button("Generate NPC"):
        npc = generate_npc(st.session_state.api_key, npc_prompt)
        st.session_state.generated_content = npc
    if "generated_content" in st.session_state:
        with st.expander("🛡️ View & Edit NPC"):
            st.session_state.generated_content = st.text_area("Modify NPC", value=st.session_state.generated_content, height=250)
        if st.button("🛒 Add to Cart"):
            st.session_state.cart["npc"].append(st.session_state.generated_content)
            save_cart()
            st.success("Added to Cart!")

def create_shop_page():
    st.header("🛒 Generate a Shop")
    shop_prompt = st.text_area("What do you already know about this shop? (Optional)")
    if st.button("Generate Shop"):
        shop = generate_shop(st.session_state.api_key, shop_prompt)
        st.session_state.generated_content = shop
    if "generated_content" in st.session_state:
        with st.expander("🛒 View & Edit Shop"):
            st.session_state.generated_content = st.text_area("Modify Shop", value=st.session_state.generated_content, height=250)
        if st.button("🛒 Add to Cart"):
            st.session_state.cart["shop"].append(st.session_state.generated_content)
            save_cart()
            st.success("Added to Cart!")

def cart_page():
    st.header("🛒 Your Cart")
    categories = list(st.session_state.cart.keys())
    selected_category = st.selectbox("📂 Select Folder", categories)
    files = st.session_state.cart[selected_category]
    selected_file = st.selectbox(f"📜 Files in {selected_category}", files)
    if selected_file:
        st.markdown("### 📖 Preview")
        st.markdown(selected_file)

def quick_actions_sidebar():
    st.sidebar.title("⚡ Quick Actions")
    st.sidebar.button("🛡️ Generate NPC")
    st.sidebar.button("🛒 Generate Shop")
    st.sidebar.button("🏰 Generate Location")
    st.sidebar.markdown("### 🔄 Recent Items")
    for item in st.session_state.cart.keys():
        for entry in st.session_state.cart[item][-3:]:
            st.sidebar.markdown(f"- {entry}")

def create_location_page():
    st.header("🏰 Generate a Location")
    location_prompt = st.text_area("What do you already know about this location? (Optional)")
    if st.button("Generate Location"):
        location = generate_location(st.session_state.api_key, location_prompt)
        st.session_state.generated_location = location
        with st.expander("Generated Location Details"):
            st.text_area("Generated Location:", location, height=250)
      
    if "generated_location" in st.session_state and st.session_state.generated_location:
            if st.button("Send to Vault!"):
                location_name = st.session_state.generated_location.split("**📜 Nom de la location** : ")[-1].split("\n")[0].replace(" ", "_")

                # Save to Dropbox
                success = write_note(f"To Sort Later/{location_name}.md", st.session_state.generated_location)

                # Notify the user
                if success:
                    st.success(f"✅ Location '{location_name}' saved to 'To Sort Later' in Obsidian Vault!")
                else:
                    st.error("❌ Failed to save Location to Obsidian Vault. Check your Dropbox connection.")

def adapt_chapter_page():
    st.header("Adapt Chapter to Campaign")
    st.write("Modify your campaign text dynamically.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_area("Original Chapter", height=200)
        st.button("Load")
    with col2:
        st.text_area("Edits Input", height=200)
    with col3:
        st.text_area("AI Output", height=200)
        st.button("Refresh")

def campaign_assistant_page():
    st.header("Campaign Assistant")
    st.write("Ask questions about past campaign details.")
    st.text_input("Enter your query:")
    st.button("Submit Query")

def encounter_generator_page():
    st.header("Encounter Generator")
    st.write("Generate encounters based on party size and details.")
    st.number_input("Party Size", min_value=1, step=1)
    st.text_input("Custom Encounter Prompt:")
    st.button("Generate Encounter")

def dungeon_generator_page():
    st.header("Dungeon Generator")
    st.write("Enter dungeon details and generate a full layout.")
    st.text_input("Dungeon Prompt:")
    st.button("Generate Dungeon")

def quest_generator_page():
    st.header("Quest Generator")
    st.write("Generate a quest based on input details.")
    st.text_input("Quest Prompt:")
    st.button("Generate Quest")

def worldbuilding_page():
    st.header("Worldbuilding Expansion")
    st.write("Auto-fill lore and expand world details.")
    st.button("Generate World Lore")

def session_work_tools_page():
    st.header("Session Work Tools")
    st.write("Tools for session intros and note assistance.")
    st.text_input("Session Details (e.g., S01):")
    st.button("Load Session History")
    
def main():
    quick_actions_sidebar()
    if st.session_state.api_key is None:
        api_key_page()
    else:
        load_cart()
        main_menu()

if __name__ == "__main__":
    main()
