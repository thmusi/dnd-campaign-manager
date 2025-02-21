import dropbox
import os
import streamlit as st
st.write("🔍 Streamlit Secrets:", st.secrets)  # Debugging step
import obsidian  # Import the Obsidian Dropbox module

# Use Streamlit secrets for Dropbox authentication
DROPBOX_ACCESS_TOKEN = st.secrets["DROPBOX_ACCESS_TOKEN"]
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def test_dropbox_upload():
    file_path = "/Obsidian-Test/test_file.md"  # Adjust to match your Obsidian folder
    content = "### Dropbox Test\nThis is a test file upload."

    try:
        dbx.files_upload(content.encode(), file_path, mode=dropbox.files.WriteMode("overwrite"))
        return f"✅ Uploaded successfully: {file_path}"
    except Exception as e:
        return f"❌ Upload failed: {e}"
DROPBOX_VAULT_PATH = "/ObsidianVault/"  # Modify this based on your vault structure

db = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_dropbox_files():
    """Lists files in the root folder of the Dropbox account."""
    try:
        files = dbx.files_list_folder("").entries
        return [file.name for file in files]  # Returns a list of file names
    except Exception as e:
        return f"Error: {e}"

def list_notes():
    """List all markdown files in the Obsidian vault stored in Dropbox."""
    try:
        result = db.files_list_folder(DROPBOX_VAULT_PATH)
        notes = [entry.name for entry in result.entries if entry.name.endswith(".md")]
        return notes
    except Exception as e:
        print(f"Error listing notes: {e}")
        return []

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

def save_ai_generated_content(title, content):
    """Save AI-generated content as a Markdown file in Obsidian via Dropbox."""
    ai_name = content.split("\n")[0].strip("# ").replace(" ", "_")  # Extract first line as title
    note_name = f"{title}_{ai_name}.md" if ai_name else f"{title}.md"
    markdown_content = f"# {title}\n\n{content}"
    
    # Debugging
    if ai_name:
        print(f"✅ AI-generated filename: {note_name}")  # Success!
    else:
        print("❌ AI name extraction failed. Using fallback title.")

    # Save to Dropbox with new path
    file_path = f"/ObsidianVault/{note_name}"
    obsidian.write_note(note_name, markdown_content)
    print(f"AI-generated content saved: {file_path}")


if __name__ == "__main__":
    # Test Dropbox Integration
    print("Listing notes:", list_notes())
    sample_note = "Test_NPC.md"
    test_content = "# Test NPC\n- Name: Eldrin the Wise\n- Race: Elf\n- Class: Wizard"
    write_note(sample_note, test_content)
    print("Reading back:", read_note(sample_note))

def list_dropbox_files():
    try:
        files = dbx.files_list_folder("").entries
        return [file.name for file in files]
    except Exception as e:
        return f"Error: {e}"
