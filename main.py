import streamlit as st
import openai
from ai import generate_npc, generate_shop, generate_location, modify_campaign_chapter
from obsidian import test_dropbox_upload, write_note, list_campaign_files, fetch_note_content
from ai import ai_search_campaign_notes

# Initialize session state for API key
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

# Sidebar Navigation
st.sidebar.title("Navigation")
menu_options = [
    "Home", "Generate NPC", "Generate Shop", "Generate Location", "Modify Campaign Chapter"
]
choice = st.sidebar.radio("Select a feature", menu_options)

def api_key_page():
    st.title("🔑 OpenAI API Key Input")
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")
    if st.button("Submit API Key"):
        if api_key:
            st.session_state.api_key = api_key
            st.success("API Key set successfully!")
            st.experimental_rerun()
        else:
            st.error("Please enter a valid API key.")

def main_menu():
    st.title("📜 D&D Campaign Manager")
    st.write("Select a feature from the sidebar.")

def generate_npc_page():
    st.header("🛡️ Generate an NPC")
    npc_prompt = st.text_area("What do you already know about this NPC? (Optional)")
    if st.button("Generate NPC"):
        npc = generate_npc(st.session_state.api_key, npc_prompt)
        st.session_state.generated_npc = npc
        st.markdown("### 🛡️ PNJ Généré")
        st.markdown(npc)
      
    if "generated_npc" in st.session_state and st.session_state.generated_npc:
            if st.button("Send to Vault!"):
                # Extract NPC name safely
                npc_name = st.session_state.generated_npc.split("**📜 Nom du PNJ** : ")[-1].split("\n")[0].replace(" ", "_")
    
                # Save to Dropbox
                success = write_note(f"To Sort Later/{npc_name}.md", st.session_state.generated_npc)
        
                # Notify the user
                if success:
                    st.success(f"✅ NPC '{npc_name}' saved to 'To Sort Later' in Obsidian Vault!")
                else:
                    st.error("❌ Failed to save NPC to Obsidian Vault. Check your Dropbox connection.")

def generate_shop_page():
    st.header("🛒 Generate a Shop")
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
      
    if "generated_shop" in st.session_state and st.session_state.generated_shop:
            if st.button("Send to Vault!"):
                import re

                # Extract AI-generated shop name using regex
                shop_match = re.search(r"\*\*📜 Nom du magasin\*\* : (.+)", st.session_state.generated_shop)

                # If found, use extracted name; otherwise, use "Generated_Shop"
                shop_name = shop_match.group(1).strip().replace(" ", "_") if shop_match else "Generated_Shop"

                # Save to Dropbox
                success = write_note(f"To Sort Later/{shop_name}.md", st.session_state.generated_shop)

                # Notify the user
                if success:
                    st.success(f"✅ Shop '{shop_name}' saved to 'To Sort Later' in Obsidian Vault!")
                else:
                    st.error("❌ Failed to save Shop to Obsidian Vault. Check your Dropbox connection.")

def generate_location_page():
    st.header("🏰 Generate a Location")
    location_prompt = st.text_area("What do you already know about this location? (Optional)")
    if st.button("Generate Location"):
        location = generate_location(st.session_state.api_key, location_prompt)
        st.session_state.generated_location = location
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

# Main execution logic
if st.session_state.api_key is None:
    api_key_page()
else:
    if choice == "Home":
        main_menu()
    elif choice == "Generate NPC":
        generate_npc_page()
    elif choice == "Generate Shop":
        generate_shop_page()
    elif choice == "Generate Location":
        generate_location_page()
