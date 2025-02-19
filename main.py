import streamlit as st
import openai

# Streamlit UI
st.title("🔑 OpenAI API Key Input")

# Ask user for API key
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

# Proceed only if an API key is entered
if api_key:
    try:
        # Initialize OpenAI client with entered key
        client = openai.OpenAI(api_key=api_key)

        # Test API Connection by listing available models
        response = client.models.list()
        available_models = [model.id for model in response.data]

        st.success("✅ API Key is valid!")
        st.write("Available OpenAI Models:", available_models)

    except openai.OpenAIError as e:
        st.error(f"❌ Invalid API Key or Connection Error: {e}")
else:
    st.warning("Please enter your OpenAI API Key to proceed.")

# Title of the app
st.title("📝 AI-Powered D&D Campaign Manager")

# Sidebar Navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Home", "NPC Generator", "Locations", "Session Logs"])

# Main page content
if page == "Home":
    st.write("Welcome to the AI-Powered D&D Campaign Manager!")
    st.write("This tool helps you manage your campaign, generate NPCs, and modify your story.")

elif page == "NPC Generator":
    st.header("🔹 Generate an NPC")

    # Form to enter NPC details
    with st.form("npc_form"):
        name = st.text_input("NPC Name", "A mysterious traveler")
        race = st.selectbox("Race", ["Human", "Elf", "Dwarf", "Orc", "Tiefling", "Halfling"])
        profession = st.text_input("Profession", "Wandering merchant")
        backstory = st.text_area("Short Backstory", "A traveler with a hidden past...")

        # Submit button
        submitted = st.form_submit_button("Generate NPC")

        if submitted:
            st.success(f"NPC Created: {name}, a {race} {profession}.")
            st.write(f"📜 **Backstory:** {backstory}")

elif page == "Locations":
    st.header("🏰 Locations")
    st.write("Manage your campaign locations here.")

elif page == "Session Logs":
    st.header("📜 Session Logs")
    st.write("Automatically log and summarize your D&D sessions.")

import streamlit as st

st.title("AI-Powered D&D Campaign Manager")

# NPC Generation
st.header("Generate an NPC")
if st.button("Generate NPC"):
    npc = generate_npc()
    st.text_area("Generated NPC:", npc, height=300)

# Location Generation
st.header("Generate a Location")
if st.button("Generate Location"):
    location = generate_location()
    st.text_area("Generated Location:", location, height=300)

# Campaign Chapter Modification
st.header("Modify a Campaign Chapter")
user_text = st.text_area("Enter existing chapter text:")
if st.button("Modify Chapter") and user_text:
    modified_text = modify_campaign_chapter(user_text)
    st.text_area("Modified Chapter:", modified_text, height=300)

# Footer
st.sidebar.write("---")
st.sidebar.write("🔮 Powered by AI & Streamlit")
