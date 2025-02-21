import dropbox
import os
import streamlit as st
st.write("🔍 Streamlit Secrets:", st.secrets)  # Debugging step
import obsidian  # Import the Obsidian Dropbox module

# Use Streamlit secrets for Dropbox authentication
DROPBOX_ACCESS_TOKEN = st.secrets["DROPBOX_ACCESS_TOKEN"]
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

DROPBOX_VAULT_PATH = "/ObsidianVault/"  # Adjust folder as needed

def read_note(note_name):
    """Read the content of a specific note from Dropbox."""
    file_path = f"{DROPBOX_VAULT_PATH}{note_name}"
    try:
        _, res = db.files_download(file_path)
        return res.content.decode("utf-8")
    except Exception as e:
        print(f"Error reading {note_name}: {e}")
        return None

def write_note(note_name, content):
    """Write or update a note in Dropbox."""
    file_path = f"{DROPBOX_VAULT_PATH}{note_name}"
    try:
        db.files_upload(content.encode("utf-8"), file_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"Successfully updated {note_name} in Dropbox.")
    except Exception as e:
        print(f"Error writing {note_name}: {e}")

def extract_ai_name(content):
    """Extract the NPC, shop, or location name from the AI-generated content."""
    lines = content.split("\n")
    for line in lines:
        match = re.search(r"\*\*Nom\*\* : (.+)", line)  # Looks for **Nom** : Name
        if match:
            return match.group(1).strip().replace(" ", "_")  # Extract and format name
    return "Unknown"

def save_ai_generated_content(title, content):
    """Save AI-generated content as a Markdown file in Obsidian via Dropbox."""
    ai_name = extract_ai_name(content)
    note_name = f"{title}_{ai_name}.md" if ai_name else f"{title}.md"
    markdown_content = f"# {title}\n\n{content}"
    
    # Debugging: Print before saving
    print(f"📝 Preview before saving:\n{markdown_content}")
    print(f"📂 File will be saved as: {note_name}")

    # Save to Dropbox with new path
    file_path = f"{DROPBOX_VAULT_PATH}{note_name}"
    print(f"📤 Uploading to Dropbox: {file_path}")

    try:
        dbx.files_upload(markdown_content.encode(), file_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"✅ Successfully uploaded: {file_path}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
