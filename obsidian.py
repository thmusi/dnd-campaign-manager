import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from datetime import datetime
import streamlit as st
import re
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account


GOOGLE_CREDENTIALS_PATH = "/etc/secrets/google_credentials.json"  # ✅ Correct Render Secret File Path

def load_google_credentials():
    """Loads Google Drive API credentials securely from a Render Secret File."""
    try:
        # ✅ Check if the secret file exists
        if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
            raise FileNotFoundError(f"❌ Secret file not found at {GOOGLE_CREDENTIALS_PATH}")

        # ✅ Read the JSON credentials file
        with open(GOOGLE_CREDENTIALS_PATH, "r") as f:
            credentials_json = f.read().strip()

        # ✅ Convert JSON string to dictionary
        credentials_dict = json.loads(credentials_json)

        # ✅ Fix newlines in the private key
        if "private_key" in credentials_dict:
            credentials_dict["private_key"] = credentials_dict["private_key"].replace("\\n", "\n")

        return service_account.Credentials.from_service_account_info(credentials_dict)

    except json.JSONDecodeError:
        st.error("❌ Invalid JSON format in Google Credentials file. Please check the secret file.")
        st.stop()

    except Exception as e:
        st.error(f"❌ Error loading Google Drive credentials: {e}")
        st.stop()

# ✅ Load credentials and check if successful
credentials = load_google_credentials()

if credentials:
    st.success("✅ Google Drive authentication successful!")
else:
    st.error("❌ Google Drive authentication failed!")
# Load credentials from environment variable or JSON file
def authenticate_google_drive():
    creds = None
    credentials_json = os.getenv("GOOGLE_DRIVE_CREDENTIALS")  # Ensure this env var is correctly set

    if credentials_json:
        creds_dict = json.loads(credentials_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/drive"])
    else:
        raise Exception("❌ Google Drive credentials not found! Ensure GOOGLE_DRIVE_CREDENTIALS is set.")

    return build("drive", "v3", credentials=creds)

# Initialize Drive Service
drive_service = authenticate_google_drive()

# Your Google Drive folder where Obsidian files will be stored
DRIVE_FOLDER_ID = "1ekTkv_vWBBcm6S7Z8wZiTEof8m8wcfwJ"

def list_campaign_files():
    """Lists all campaign-related files stored in Google Drive."""
    try:
        files = list_drive_files()  # Uses Google Drive function
        return [file["name"] for file in files]  # Returns only file names
    except Exception as e:
        print(f"❌ Error listing campaign files: {e}")
        return []

def write_note(note_name, content):
    """Saves a note as a Markdown file in Obsidian via Google Drive."""
    note_name = f"{note_name.replace(' ', '_')}.md"

    # Ensure the directory exists
    vault_path = "obsidian_vault"
    os.makedirs(vault_path, exist_ok=True)  # ✅ Create if missing

    file_path = os.path.join(vault_path, note_name)

    # Save locally before upload
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    upload_file(file_path)  # ✅ Upload to Google Drive
    st.success(f"✅ Note saved to Google Drive: {note_name}")
    return note_name

# Upload a file to Google Drive
def upload_file(file_path, drive_folder_id=DRIVE_FOLDER_ID):
    """Uploads a file to Google Drive inside the specified folder."""
    file_metadata = {"name": os.path.basename(file_path), "parents": [drive_folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"✅ File uploaded: {file.get('id')}")
    return file.get("id")

# List all files in the Google Drive folder
def list_drive_files(drive_folder_id=DRIVE_FOLDER_ID):
    """Lists all files in the given Google Drive folder."""
    results = drive_service.files().list(q=f"'{drive_folder_id}' in parents",
                                         fields="files(id, name)").execute()
    return results.get("files", [])

# Download a file from Google Drive
def download_file(file_id, output_path):
    """Downloads a file from Google Drive to a local path."""
    request = drive_service.files().get_media(fileId=file_id)
    with open(output_path, "wb") as file:
        file.write(request.execute())
    print(f"✅ File downloaded: {output_path}")

def save_to_vault(content, filename="generated_content.md"):
    """Saves the modified content to the user's Obsidian-Google Drive vault only when manually triggered."""
    vault_path = "obsidian_vault"
    os.makedirs(vault_path, exist_ok=True)  # Ensure directory exists
    
    # ✅ Ensure filename has a reasonable length limit (max 50 chars, excluding extension)
    base_filename, ext = os.path.splitext(filename)
    base_filename = base_filename[:50]  # Trim name to avoid system limit
    filename = f"{base_filename}{ext or '.md'}"  # Ensure .md extension

    # ✅ Remove special characters and spaces from filename
    filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)

    file_path = os.path.join(vault_path, filename)

    # ✅ Save locally before upload
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    upload_file(file_path)  # ✅ Upload to Google Drive
    st.success(f"✅ File saved successfully to Google Drive: {filename}")

# Retained non-Dropbox functions from original obsidian.py
# Additional Obsidian-related utilities and Markdown processing functions

def format_markdown_header(text):
    """Formats text as a Markdown header."""
    return f"# {text}\n"

def create_obsidian_note(title, content):
    """Creates an Obsidian-compatible Markdown note."""
    note_content = format_markdown_header(title) + "\n" + content
    file_name = f"{title.replace(' ', '_')}.md"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(note_content)
    print(f"📝 Note created: {file_name}")
    return file_name

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
    for keyword in keywords:
        count = content.lower().count(keyword.lower())
        weight = keyword_weights.get(keyword, 1)
        score += count * weight
    if "Whitestone" in file_path:
        score *= 1.5
    days_since_modified = (datetime.now().timestamp() - last_modified) / 86400
    recency_multiplier = max(0.5, 1 - (days_since_modified / 365))
    score *= recency_multiplier
    return score

def get_relevant_notes(query, vault_path):
    """Fetches the most relevant notes based on keyword search."""
    keywords = query.split()
    keyword_weights = {"Whitestone": 2, "NPC": 1.5}
    index = build_index(vault_path, keywords, keyword_weights)
    threshold = 5
    relevant_notes = [note for note in index if note["score"] >= threshold]
    return relevant_notes[:5]

def save_ai_generated_content(title, content):
    """Save AI-generated content as a Markdown file in Obsidian via Google Drive."""
    note_name = f"{title.replace(' ', '_')}.md"
    markdown_content = f"# {title}\n\n{content}"
    file_path = os.path.join("obsidian_vault", note_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    upload_file(file_path)
    print(f"AI-generated content saved: {note_name}")
