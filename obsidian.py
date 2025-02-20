import dropbox
import os
from dotenv import load_dotenv
import obsidian  # Import the Obsidian Dropbox module

# Load environment variables
load_dotenv()
DROPBOX_ACCESS_TOKEN = os.getenv("b2a259qsha239dg")
DROPBOX_VAULT_PATH = "/ObsidianVault/"  # Modify this based on your vault structure

db = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

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
    note_name = f"{title.replace(' ', '_')}.md"
    markdown_content = f"# {title}\n\n{content}"
    obsidian.write_note(note_name, markdown_content)
    print(f"AI-generated content saved: {note_name}")

if __name__ == "__main__":
    # Test Dropbox Integration
    print("Listing notes:", list_notes())
    sample_note = "Test_NPC.md"
    test_content = "# Test NPC\n- Name: Eldrin the Wise\n- Race: Elf\n- Class: Wizard"
    write_note(sample_note, test_content)
    print("Reading back:", read_note(sample_note))
