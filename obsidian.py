import dropbox
import os
import streamlit as st
st.write("🔍 Streamlit Secrets:", st.secrets)  # Debugging step
import obsidian  # Import the Obsidian Dropbox module
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Use Streamlit secrets for Dropbox authentication
DROPBOX_ACCESS_TOKEN = st.secrets["DROPBOX_ACCESS_TOKEN"]
db = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

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

@st.cache_data(ttl=300)  # Cache file list for 5 minutes
def cached_list_campaign_files():
    return list_campaign_files()

# Use cached function
files = cached_list_campaign_files()

def build_index(vault_path, keywords, keyword_weights):
    """
    Scan the Obsidian vault directory and compute a relevance score for each .md file.
    """
    index = []
    for root, dirs, files in os.walk(vault_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                last_modified = os.path.getmtime(file_path)
                score = compute_keyword_score(content, file_path, last_modified, keywords, keyword_weights)
                index.append({
                    "file_path": file_path,
                    "score": score,
                    "last_modified": last_modified,
                    "content": content
                })
    # Sort the index in descending order by score
    index.sort(key=lambda x: x["score"], reverse=True)
    return index

def compute_keyword_score(content, file_path, last_modified, keywords, keyword_weights):
    """
    Compute a relevance score for the note based on:
      - Keyword frequency (weighted)
      - Folder-based weighting (bonus if file path contains target folder names)
      - Recency (more recent notes score higher)
    """
    score = 0
    # Calculate base score from keyword frequency
    for keyword in keywords:
        count = content.lower().count(keyword.lower())
        weight = keyword_weights.get(keyword, 1)
        score += count * weight
    
    # Folder-based bonus example: if the file is in a folder named "Whitestone"
    if "Whitestone" in file_path:
        score *= 1.5
    
    # Recency factor: calculate how many days ago the note was modified
    days_since_modified = (datetime.now().timestamp() - last_modified) / 86400
    # Use a decay function: full weight for notes modified within 1 year, then decreasing.
    recency_multiplier = max(0.5, 1 - (days_since_modified / 365))
    score *= recency_multiplier
    
    return score

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
    print(f"Attempting to save: {file_path}")  # Debugging output
    try:
        db.files_upload(content.encode("utf-8"), file_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"✅ Successfully updated {note_name} in Dropbox.")
        return True
    except dropbox.exceptions.AuthError:
        print("❌ Dropbox authentication failed. Check your access token.")
        return False
    except Exception as e:
        print(f"❌ Error writing {note_name}: {e}")
        return False

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

def list_dropbox_files():
    try:
        files = dbx.files_list_folder("").entries
        return [file.name for file in files]
    except Exception as e:
        return f"Error: {e}"

def list_campaign_files():
    """Lists all campaign-related files in the Dropbox folder."""
    try:
        result = dbx.files_list_folder(DROPBOX_FOLDER_PATH)
        files = [entry.name for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]
        return files
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def get_relevant_notes(query, vault_path):
    # Extract keywords from the query; here we simply split the query, but you can enhance this.
    keywords = query.split()
    
    # Define keyword weights – adjust these values based on importance.
    keyword_weights = {
        "Whitestone": 2,
        "NPC": 1.5,
        # Add other keywords and their weights as needed.
    }
    
    # Build the index for the current vault
    index = build_index(vault_path, keywords, keyword_weights)
    
    # Optional: filter out notes below a certain score threshold
    threshold = 5  # Adjust this threshold as needed
    relevant_notes = [note for note in index if note["score"] >= threshold]
    
    # Limit to top 5 results (or any number you prefer)
    return relevant_notes[:5]


def fetch_note_content(file_name):
    """Fetches the content of a campaign note from Dropbox."""
    file_path = f"{DROPBOX_FOLDER_PATH}/{file_name}"
    try:
        metadata, res = dbx.files_download(file_path)
        return res.content.decode("utf-8")
    except Exception as e:
        print(f"Error fetching note: {e}")
        return None
