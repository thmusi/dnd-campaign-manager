import streamlit as st

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

# Footer
st.sidebar.write("---")
st.sidebar.write("🔮 Powered by AI & Streamlit")
