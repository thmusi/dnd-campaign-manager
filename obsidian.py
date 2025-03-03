import os
import json
from datetime import datetime
import streamlit as st
import re
import requests
from urllib.parse import urlencode

# Load Dropbox credentials from Render environment variables
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
OAUTH_REDIRECT_URI = "https://dnd-campaign-manager.onrender.com/oauth_callback"  # Replace with your actual Render app URL

def get_authorization_url():
    """Generate a Dropbox authorization URL for the user."""
    params = {
        "client_id": DROPBOX_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": OAUTH_REDIRECT_URI,
        "token_access_type": "offline"  # Ensures we get a refresh token
    }
    return f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"

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
