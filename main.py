import streamlit as st

# Title of the app
st.title("📝 AI-Powered D&D Campaign Manager")

# Sidebar Navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Home", "NPCs", "Locations", "Session Logs"])

# Main page content
if page == "Home":
    st.write("Welcome to the AI-Powered D&D Campaign Manager!")
    st.write("This tool will help you manage your campaign, generate NPCs, and modify your story.")

elif page == "NPCs":
    st.write("🔹 NPC Management")
    st.write("Here, you will be able to generate, edit, and manage NPCs.")

elif page == "Locations":
    st.write("🏰 Locations")
    st.write("This section will allow you to create and manage campaign locations.")

elif page == "Session Logs":
    st.write("📜 Session Logs")
    st.write("Automatically log and summarize your D&D sessions.")

# Footer
st.sidebar.write("---")
st.sidebar.write("🔮 Powered by AI & Streamlit")
