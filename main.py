import streamlit as st
import openai
from ai import generate_npc, generate_location, modify_campaign_chapter

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
        # Form to enter NPC details
        with st.form("npc_form"):
            name = st.text_input("NPC Name", "A mysterious traveler")
            race = st.selectbox("Race", ["Human", "Elf", "Dwarf", "Orc", "Tiefling", "Halfling"])
            profession = st.text_input("Profession", "Wandering merchant")
            backstory = st.text_area("Short Backstory", "A traveler with a hidden past...")
            
            # Submit button
            submitted = st.form_submit_button("Generate NPC")
        
        if submitted:
            npc = generate_npc(api_key)
            st.text_area("Generated NPC:", npc, height=250)
        st.subheader("🛡️ Generate an NPC")
        if st.button("Create NPC"):
            npc = generate_npc(api_key)
            st.text_area("Generated NPC:", npc, height=250)

        # Generate Location
        # Generate Shop
        st.subheader("🛒 Generate a Shop")
        shop_type = st.selectbox("Select Shop Type", [
            "General Store", "Blacksmith", "Alchemy Shop", "Magic Shop", "Tavern", 
            "Jewelry Store", "Weapon Shop", "Armorer", "Fletcher", "Bookstore", "Stable",
            "Enchanter", "Herbalist", "Bakery", "Tailor", "Carpenter"
        ])
        if st.button("Create Shop"):
            shop = generate_location(api_key)
            st.text_area(f"Generated {shop_type}:", shop, height=250)
        st.subheader("🏰 Generate a Location")
        if st.button("Create Location"):
            location = generate_location(api_key)
            st.text_area("Generated Location:", location, height=250)

        # Modify Campaign Chapter
        st.subheader("📖 Modify a Campaign Chapter")
        user_text = st.text_area("Enter existing chapter text:")
        if st.button("Modify Chapter") and user_text:
            modified_text = modify_campaign_chapter(user_text, api_key)
            st.text_area("Modified Chapter:", modified_text, height=250)

    except openai.OpenAIError as e:
        st.error(f"❌ Invalid API Key or Connection Error: {e}")
else:
    st.warning("Please enter your OpenAI API Key to proceed.")
