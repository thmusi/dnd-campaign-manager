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
            # Extract NPC name safely
            npc_name = st.session_state.generated_npc.split("**📜 Nom du PNJ** : ")[-1].split("\n")[0].replace(" ", "_")

            # Save to Dropbox
            success = write_note(f"To Sort Later/{npc_name}.md", st.session_state.generated_npc)
        
            # Notify the user
            if success:
                st.success(f"✅ NPC '{npc_name}' saved to 'To Sort Later' in Obsidian Vault!")
            else:
                st.error("❌ Failed to save NPC to Obsidian Vault. Check your Dropbox connection.")
     
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

                # Save to Dropbox
                success = write_note(f"To Sort Later/{location_name}.md", st.session_state.generated_location)

                # Notify the user
                if success:
                    st.success(f"✅ Location '{location_name}' saved to 'To Sort Later' in Obsidian Vault!")
                else:
                    st.error("❌ Failed to save Location to Obsidian Vault. Check your Dropbox connection.")

            
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

