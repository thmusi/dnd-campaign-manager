    import streamlit as st
import openai
from ai import generate_npc, generate_shop, modify_campaign_chapter
from obsidian import test_dropbox_upload, write_note  # Remove list_dropbox_files import

# Streamlit UI
st.title("🔑 OpenAI API Key Input")

# Ask user for API key
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

# Proceed only if an API key is entered
if api_key:
    try:
        # Test API Connection
        client = openai.OpenAI(api_key=api_key)
        test_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'Hello!'"}]
        )

        st.success("✅ API Key is valid! You can now generate D&D content.")

        # --- AI Content Generation UI ---
        st.header("📜 Generate D&D Content")

        # Generate NPC
        st.subheader("🛡️ Generate an NPC")
        npc_prompt = st.text_area("What do you already know about this NPC? (Optional)")
        if st.button("Generate NPC"):
            npc = generate_npc(api_key, npc_prompt)
            st.session_state.generated_npc = npc  # Store generated NPC
            st.markdown("### 🛡️ PNJ Généré")
            st.markdown(npc)
        
        if "generated_npc" in st.session_state and st.session_state.generated_npc:
            if st.button("Send to Vault!"):
                npc_name = st.session_state.generated_npc.split("**📜 Nom du PNJ** : ")[-1].split("\n")[0].replace(" ", "_")
                write_note(f"To Sort Later/{npc_name}.md", st.session_state.generated_npc)
                st.success("✅ NPC saved to 'To Sort Later' in Obsidian Vault!")
     
        # Generate Location
        st.subheader("🏰 Generate a Location")
        location_prompt = st.text_area("What do you already know about this location? (Optional)")
        if st.button("Generate Location"):
            location = generate_location(api_key, location_prompt)
            st.session_state.generated_location = location  # Store generated location
            st.text_area("Generated Location:", location, height=250)
        
        if "generated_location" in st.session_state and st.session_state.generated_location:
            if st.button("Send to Vault!"):
                location_name = st.session_state.generated_location.split("**📜 Nom de la location** : ")[-1].split("\n")[0].replace(" ", "_")
                write_note(f"To Sort Later/{location_name}.md", st.session_state.generated_location)
                st.success("✅ Location saved to 'To Sort Later' in Obsidian Vault!")
            
        # Generate Shop
        st.subheader("🛒 Generate a Shop")
        shop_type = st.selectbox("Select Shop Type", [
            "General Store", "Blacksmith", "Alchemy Shop", "Magic Shop", "Tavern", 
            "Jewelry Store", "Weapon Shop", "Armorer", "Fletcher", "Bookstore", "Stable",
            "Enchanter", "Herbalist", "Bakery", "Tailor", "Carpenter"
        ])
        shop_prompt = st.text_area("What do you already know about this shop? (Optional)")
        if st.button("Generate Shop"):
            shop = generate_shop(api_key, shop_type, shop_prompt)
            st.session_state.generated_shop = shop  # Store generated shop
            st.text_area(f"Generated {shop_type}:", shop, height=250)
        
        if "generated_shop" in st.session_state and st.session_state.generated_shop:
            if st.button("Send to Vault!"):
                shop_name = st.session_state.generated_shop.split("**📜 Nom du magasin** : ")[-1].split("\n")[0].replace(" ", "_")
                write_note(f"To Sort Later/{shop_name}.md", st.session_state.generated_shop)
                st.success("✅ Shop saved to 'To Sort Later' in Obsidian Vault!")
            
        # Modify Campaign Chapter
        st.subheader("📖 Modify a Campaign Chapter")
        user_text = st.text_area("Enter existing chapter text:")
        chapter_prompt = st.text_area("What changes should be made? (Optional)")
        if st.button("Generate Modified Chapter") and user_text:
            modified_text = modify_campaign_chapter(user_text, api_key, chapter_prompt)
            st.session_state.generated_chapter = modified_text  # Store generated chapter
            st.text_area("Modified Chapter:", modified_text, height=250)
        
        if "generated_chapter" in st.session_state and st.session_state.generated_chapter:
            if st.button("Send to Vault!"):
                write_note("ToSortLater.md", st.session_state.generated_chapter)
                st.success("✅ Modified campaign chapter saved to 'To Sort Later' in Obsidian Vault!")

    except openai.OpenAIError as e:
        st.error(f"❌ Invalid API Key or Connection Error: {e}")
else:
    st.warning("Please enter your OpenAI API Key to proceed.")

