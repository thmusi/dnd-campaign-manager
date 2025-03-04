import os
import json
from datetime import datetime
import streamlit as st
import re
import requests
from urllib.parse import urlencode
import secrets  # Fix NameError
import base64  # Fix for base64 module
import hashlib

# Ensure the environment variable is loaded
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

if not DROPBOX_ACCESS_TOKEN:
    print("⚠️ Warning: DROPBOX_ACCESS_TOKEN is not set. Authentication may fail.")

# Load Dropbox credentials from Render environment variables
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
OAUTH_REDIRECT_URI = "https://dnd-campaign-manager.onrender.com"  # Replace with your actual Render app URL

# Generate a PKCE code verifier and challenge
def generate_pkce():
    code_verifier = secrets.token_urlsafe(64)[:128]  # Generate a random 43-128 char string
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")
    return code_verifier, code_challenge

def get_authorization_url():
    """Generate a Dropbox authorization URL with PKCE."""
    code_verifier, code_challenge = generate_pkce()
    
    # Store the code_verifier temporarily
    os.environ["DROPBOX_CODE_VERIFIER"] = code_verifier

    params = {
        "client_id": DROPBOX_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": OAUTH_REDIRECT_URI,
        "token_access_type": "offline",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    return f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"

def exchange_code_for_tokens(auth_code):
    """Exchange an authorization code for Dropbox access and refresh tokens."""
    token_url = "https://api.dropbox.com/oauth2/token"

    data = {
        "code": auth_code,
        "grant_type": "authorization_code",
        "client_id": os.getenv("DROPBOX_CLIENT_ID"),
        "client_secret": os.getenv("DROPBOX_CLIENT_SECRET"),
        "redirect_uri": "https://dnd-campaign-manager.onrender.com"  # Must match Dropbox settings
    }

    print("🔍 Sending request to Dropbox API...")
    sys.stdout.flush()  # Force logs to show immediately

    response = requests.post(token_url, data=data)
    tokens = response.json()

    print("🔍 Full Dropbox API Response:", tokens)
    sys.stdout.flush()  # Ensure logs are displayed immediately

    if "error" in tokens:
        print(f"❌ Dropbox Authentication Error: {tokens.get('error_description', 'No description provided')}")
        sys.stdout.flush()

    return tokens if "access_token" in tokens else None

        
def get_access_token():
    """Retrieve a valid Dropbox access token, refreshing if necessary."""
    access_token = os.getenv("DROPBOX_ACCESS_TOKEN")

    if not access_token:
        print("🔄 Access token missing or expired. Refreshing...")
        access_token = refresh_access_token()

    return access_token

def refresh_access_token():
    """Refresh the Dropbox access token using the stored refresh token."""
    token_url = "https://api.dropbox.com/oauth2/token"

    data = {
        "refresh_token": os.getenv("DROPBOX_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
        "client_id": os.getenv("DROPBOX_CLIENT_ID"),
        "client_secret": os.getenv("DROPBOX_CLIENT_SECRET"),
    }

    response = requests.post(token_url, data=data)
    tokens = response.json()

    if "access_token" in tokens:
        print("🔄 Access token refreshed successfully!")
        os.environ["DROPBOX_ACCESS_TOKEN"] = tokens["access_token"]  # Store in memory
        return tokens["access_token"]
    else:
        print("❌ Error refreshing token:", tokens)
        return None

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

def write_note(filename, content, obsidian_folder="/ObsidianNotes"):
    """Saves a Markdown note to the Dropbox-linked Obsidian folder."""
    global DROPBOX_ACCESS_TOKEN  # Ensure we use the global variable

    if not DROPBOX_ACCESS_TOKEN:
        print("⚠️ Warning: DROPBOX_ACCESS_TOKEN is missing, attempting to refresh...")
        DROPBOX_ACCESS_TOKEN = refresh_access_token()  # Try refreshing the token

    if not DROPBOX_ACCESS_TOKEN:  # Still missing?
        raise ValueError("❌ Dropbox authentication failed! Please reconnect.")

    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    dropbox_path = f"{obsidian_folder}/{filename}.md"

    try:
        dbx.files_upload(content.encode("utf-8"), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        return f"✅ Note saved to {dropbox_path}"
    except dropbox.exceptions.AuthError:
        return "❌ Dropbox authentication error! Please reconnect."
    except Exception as e:
        return f"❌ Error saving note: {e}"

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
