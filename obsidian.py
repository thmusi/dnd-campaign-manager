import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from datetime import datetime
import streamlit as st

credentials_info = json.loads(st.secrets["google_drive"])
credentials = service_account.Credentials.from_service_account_info(credentials_info)

drive_service = build("drive", "v3", credentials=credentials)

# Your Google Drive folder where Obsidian files will be stored
DRIVE_FOLDER_ID = "1ekTkv_vWBBcm6S7Z8wZiTEof8m8wcfwJ"

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
