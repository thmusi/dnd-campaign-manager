import streamlit as st
import chromadb
import os
import json
import subprocess
import yaml
import openai
from pathlib import Path
import pandas as pd
import time



CHROMA_DB_PATH = "chroma_db/"
CONFIG_PATH = "config.yaml"
MODIFICATION_TRACKER = "modification_tracker.yaml"

# Load configuration from config.yaml
def load_config():
    try:
        with open(CONFIG_PATH, "r") as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError:
        st.error("⚠️ Error reading config.yaml. Check file format.")
        return {}

def save_config(config):
    with open(CONFIG_PATH, "w") as file:
        yaml.safe_dump(config, file)

# Initialize ChromaDB client
db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = db.get_or_create_collection("campaign_notes")

# Load config
config = load_config()
OBSIDIAN_VAULT_PATH = config.get("obsidian_vault_path", "obsidian_vault")
FOLDERS_TO_EMBED = set(config.get("folders_to_embed", []))


        
# Ensure necessary directories exist
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
os.makedirs(OBSIDIAN_VAULT_PATH, exist_ok=True)

def embed_selected_folders(folders_to_embed, vault_path=OBSIDIAN_VAULT_PATH):
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = db.get_or_create_collection(name="campaign_notes")

    for folder in folders_to_embed:
        full_folder_path = os.path.join(vault_path, folder)

        if os.path.exists(full_folder_path):
            for root, _, files in os.walk(full_folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    collection.add(documents=[content], ids=[file_path])
                    print(f"✅ Embedded: {file_path}")
        else:
            print(f"⚠️ Folder does not exist: {full_folder_path}")



# Function to list stored embeddings
def list_embeddings():
    docs = collection.get()
    return docs if docs else {"ids": [], "documents": []}

# Function to remove an embedding
def remove_embedding(embedding_id):
    collection.delete(ids=[embedding_id])
    st.success(f"✅ Removed embedding {embedding_id}")

# Function to manually add an embedding
import subprocess

def add_embedding_and_push(embedding_data, embedding_file="embeddings.json", vault_path="obsidian_vault"):
    """
    Adds new embedding data and automatically saves it to GitHub.
    """
    try:
        # Load existing embeddings
        if os.path.exists(embedding_file):
            with open(embedding_file, "r") as f:
                embeddings = json.load(f)
        else:
            embeddings = []

        # Add new embedding
        embeddings.append(embedding_data)

        # Save embeddings locally
        with open(embedding_file, "w") as f:
            json.dump(embeddings, f, indent=4)

        # GitHub Operations
        repo_path = os.path.join(vault_path, ".git")
        if not os.path.exists(repo_path):
            print("⚠️ Vault is not a Git repository. Cloning again...")
            subprocess.run(["rm", "-rf", vault_path])  # Remove old folder
            subprocess.run(["git", "clone", "GITHUB_REPO_URL", vault_path])  # Clone fresh copy

        os.chdir(vault_path)
        subprocess.run(["git", "pull"])  # Ensure latest updates
        subprocess.run(["git", "add", embedding_file])
        subprocess.run(["git", "commit", "-m", "Updated embeddings"])
        subprocess.run(["git", "push"])
        os.chdir("..")  # Return to previous directory

        print("✅ Embeddings added and pushed to GitHub successfully!")

    except Exception as e:
        print(f"❌ Error handling embeddings: {e}")

# Function to retrieve relevant embeddings
from utils import summarize_text, chunk_text

def retrieve_relevant_embeddings(query, top_k=3, max_tokens=3000, query_type=None):
    """Retrieve relevant embeddings with weighted folder importance and apply chunking & summarization if needed."""
    db = chromadb.PersistentClient(path="chroma_db")
    collection = db.get_or_create_collection("campaign_notes")

    # ✅ FIXED: Added missing commas at the end of dictionary entries
    folder_weights = {
        "/s": {"Rulebooks/Spells": 3},  
        "/c": {"A. Campaign": 2, "C. Inspiration": 2, "B. Exandria": 1},  
        "/r": {"Rulebooks": 3},  
        "/g": {},  # General queries
        "generate_npc": {"B. Exandria": 3, "C. Inspiration": 1, "A. Campaign": 2},  
        "session_management": {"A. Campaign": 3, "A. Campaign/2. Session Plans + Logs": 3},  
        "quest_generator": {"A. Campaign": 2, "E. Ideas": 1, "B. Exandria": 2, "C. Inspiration": 2},  
        "dungeon_generator": {"A. Campaign": 1, "E. Ideas": 1, "B. Exandria": 2, "Rulebooks": 2, "C. Inspiration": 2},  
        "encounter_generator": {"A. Campaign": 1, "E. Ideas": 1, "B. Exandria": 2, "Rulebooks": 2, "C. Inspiration": 1},  
        "adapt_chapter": {"C. Inspiration/C.1. Campaign Books": 3, "A. Campaign/2. Session Plans + Logs": 3, "C. Inspiration/C.2. Process": 3},  
        "create_shop": {"B. Exandria": 3, "A. Campaign": 2},  
        "create_location": {"B. Exandria": 3, "A. Campaign": 2},  
        "worldbuilding": {}  
    }

    # ✅ FIXED: Properly get the folder weights
    weights = folder_weights.get(query_type, {"general": 1})
    results = collection.query(query_texts=[query], n_results=top_k * 2)  

    # Sort documents based on their folder priority
    weighted_docs = []
    for doc, metadata_list in zip(results.get("documents", []), results.get("metadatas", [])):
        if isinstance(metadata_list, list) and metadata_list:  
            metadata = metadata_list[0]  # Take the first metadata dictionary if a list
        elif isinstance(metadata_list, dict):  
            metadata = metadata_list  # Directly use it if it's already a dict
        else:
            metadata = {}  # Default empty dict if metadata is missing

    folder = metadata.get("source_folder", "general")  # ✅ Now metadata is safely accessed
    weight = weights.get(folder, 0)
    weighted_docs.append((doc, weight))

    # ✅ FIXED: Sort documents by weight correctly
    weighted_docs.sort(key=lambda x: x[1], reverse=True)
    sorted_docs = [str(doc) if isinstance(doc, list) else doc for doc, _ in weighted_docs[:top_k]]  # ✅ Convert lists to strings
    combined_text = "\n\n".join(sorted_docs)  # ✅ Now all items are strings

    # ✅ FIXED: Ensure text is summarized if too long
    if len(combined_text.split()) > max_tokens:
        combined_text = summarize_text(combined_text, max_tokens=max_tokens // 2)

    # ✅ FIXED: Chunk text correctly
    final_docs = chunk_text(combined_text, max_tokens=max_tokens)

    return final_docs

# Function to pull the latest GitHub Vault updates
def pull_github_vault():
    """Pulls the latest changes from the secret GitHub Vault repository."""
    GITHUB_USERNAME = "thmusi"
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    if not GITHUB_TOKEN:
        st.error("❌ GITHUB_TOKEN is missing! Set it in Render Environment Variables.")
        return

    repo_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/thmusi/my-obsidian-vault.git"

    # If the folder exists but is not a valid Git repo, delete and re-clone
    git_dir = os.path.join(OBSIDIAN_VAULT_PATH, ".git")
    if os.path.exists(OBSIDIAN_VAULT_PATH) and not os.path.exists(git_dir):
        st.warning("⚠️ obsidian_vault exists but is not a Git repository. Deleting and re-cloning...")
        subprocess.run(["rm", "-rf", OBSIDIAN_VAULT_PATH], check=True)

    if not os.path.exists(OBSIDIAN_VAULT_PATH):
        try:
            subprocess.run(["git", "clone", repo_url, OBSIDIAN_VAULT_PATH], check=True)
            st.success("✅ Cloned the secret GitHub Vault repository!")
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Git clone failed: {e}")
            return

    try:
        subprocess.run(["git", "-C", OBSIDIAN_VAULT_PATH, "remote", "set-url", "origin", repo_url], check=True)
        subprocess.run(["git", "-C", OBSIDIAN_VAULT_PATH, "pull", "origin", "main"], check=True)        
        st.success("✅ Pulled latest changes from the secret Vault!")
    except subprocess.CalledProcessError as e:
        st.error(f"❌ Git pull failed: {e}")


# Function to detect modified files and re-embed them
def reembed_modified_files():
    """Lists all markdown and PDF files and allows manual selection for embedding."""
    updated_files = []

    for root, _, files in os.walk(OBSIDIAN_VAULT_PATH):
        # If folders_to_embed is empty, allow all files
        if FOLDERS_TO_EMBED and not any(folder in root for folder in FOLDERS_TO_EMBED):
            continue  

        for file in files:
            if file.endswith((".md", ".pdf", ".json")):  # Include PDFs & JSON
                file_path = os.path.join(root, file)
                updated_files.append(file_path)

    if updated_files:
        st.subheader("📂 Select Files to Re-Embed")
        selected_files = st.multiselect("Choose files to embed:", updated_files)

        if st.button("🔄 Re-Embed Selected Files"):
            for file_path in selected_files:
                ext = os.path.splitext(file_path)[1].lower()

                if ext == ".pdf":
                    try:
                        content = extract_text(file_path).strip()  # Extract text from PDFs
                    except Exception as e:
                        st.error(f"Error extracting text from {file_path}: {e}")
                        continue  # Skip problematic PDFs
                else:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                if content.strip():  # Ensure text is not empty
                    add_embedding(content, {"source": file_path})

            st.success(f"✅ Re-embedded {len(selected_files)} files!")
    else:
        st.info("No modified files to re-embed.")

# Function to load last update timestamp
def load_last_update():
    config_path = os.path.join(CHROMA_DB_PATH, "last_update.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            return config.get("last_update", 0)
    return 0

# Function to save last update timestamp
def save_last_update():
    config_path = os.path.join(CHROMA_DB_PATH, "last_update.json")
    with open(config_path, "w") as f:
        json.dump({"last_update": os.path.getmtime(OBSIDIAN_VAULT_PATH)}, f)

def get_all_folders(base_path):
    """Retrieve all folders inside the Obsidian Vault, excluding .git."""
    folder_list = []
    for root, dirs, _ in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith(".git")]  # Exclude .git folders
        for directory in dirs:
            full_path = os.path.relpath(os.path.join(root, directory), base_path)
            folder_list.append(full_path)
    return sorted(folder_list)

def build_folder_tree(base_path):
    """Recursively build a nested dictionary of folders inside the Obsidian Vault."""
    folder_tree = {}
    for root, dirs, _ in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith(".git")]  # Exclude .git folders
        rel_path = os.path.relpath(root, base_path)
        parts = rel_path.split(os.sep) if rel_path != '.' else []
        node = folder_tree
        for part in parts:
            node = node.setdefault(part, {})
    return folder_tree

COLORS = ["#FF5733", "#FF8D1A", "#FFC300", "#DAF7A6", "#33FF57", "#1AFFD5", "#1A8DFF", "#5733FF"]

def display_folder_tree(folder_tree, base_path, folders_to_embed, config, level=0):
    """Recursively display folders with nested layout support."""
    color = COLORS[level % len(COLORS)]  # Cycle through colors for each level
    for folder, subfolders in folder_tree.items():
        folder_path = os.path.join(base_path, folder)
        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * level  # Indentation for nested folders
        
        with st.container():
            cols = st.columns([0.8, 0.2])  # Create a two-column layout for better button placement
            with cols[0]:
                st.markdown(
                    f"{indent}<span style='color:{color}; font-weight:bold;'>📂 {folder}</span>",
                    unsafe_allow_html=True
                )
            with cols[1]:
                if folder_path not in folders_to_embed:
                    if st.button(f"➡", key=f"add_{folder_path}"):
                        folders_to_embed.append(folder_path)
                        config["folders_to_embed"] = folders_to_embed
                        save_config(config)
                        st.rerun()
        
        # Recursively call for subfolders
        display_folder_tree(subfolders, folder_path, folders_to_embed, config, level + 1)

def get_folder_structure(base_path):
    """Creates a nested dictionary representing the folder structure."""
    folder_tree = {}
    if not os.path.exists(base_path):
        st.error(f"🚨 Error: Vault path '{base_path}' does not exist!")
        return folder_tree
    
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith(".git")]  # Exclude .git folders
        rel_path = os.path.relpath(root, base_path)
        parts = rel_path.split(os.sep) if rel_path != '.' else []
        node = folder_tree
        for part in parts:
            node = node.setdefault(part, {})
        
        # Store filenames inside the structure for embedding
        node["__files__"] = files
    return folder_tree

def load_modification_tracker():
    """Loads the modification tracker file to track folder updates."""
    if os.path.exists(MODIFICATION_TRACKER):
        with open(MODIFICATION_TRACKER, "r") as file:
            return yaml.safe_load(file)
    return {}

def save_modification_tracker(modification_data):
    """
    Saves the modification timestamps of folders after embedding.
    """
    with open("modification_tracker.yaml", "w") as f:
        yaml.dump(modification_data, f)

def flatten_folder_structure(folder_tree, parent_path="", depth=0):
    """Flattens the nested folder dictionary into a list with indentation levels and filenames."""
    folder_list = []
    for folder, subfolders in folder_tree.items():
        if folder == "__files__":
            continue  # Skip internal file storage key
        full_path = f"{parent_path}/{folder}" if parent_path else folder
        indent = "➡️" * (depth + 1) + " "  # Arrows to indicate depth
        folder_list.append((full_path, indent + folder, depth))
        folder_list.extend(flatten_folder_structure(subfolders, full_path, depth + 1))
    return folder_list

def check_folder_modifications(all_folders, chroma_db_path, vault_path):
    modification_data = load_modification_tracker()  
    modified_folders = {}

    for folder_path, _, _ in all_folders:
        full_path = os.path.join(vault_path, folder_path)
        latest_mod_time = max(
            (os.path.getmtime(os.path.join(root, f)) for root, _, files in os.walk(full_path) for f in files),
            default=0
        )

        last_tracked_time = modification_data.get(folder_path, 0)

        if latest_mod_time > last_tracked_time:
            modified_folders[folder_path] = "⚠️ Modified"
            modification_data[folder_path] = latest_mod_time  # Update timestamp
        else:
            modified_folders[folder_path] = "✅ Embedded"

    # Save updated modification tracker
    save_modification_tracker(modification_data)

    return modified_folders


def get_subfolders(tree, path):
    """Returns the subfolder dictionary at a given path."""
    node = tree
    for part in path.split("/"):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node

def load_selected_folders():
    """Load stored selected folders from config.yaml to persist across deployments."""
    config = load_config()
    return set(config.get("folders_to_embed", []))  # Return as a set for easy updates

def save_selected_folders(folders):
    """Save the selected folders persistently to config.yaml."""
    config = load_config()
    config["folders_to_embed"] = list(folders)  # Convert back to list for YAML
    save_config(config)

def reset_folder_status_on_pull(all_folders, config):
    # Initialize all folders as "Not Embedded" if not in config.yaml
    folder_statuses = {}
    
    for folder_path, _, _ in all_folders:
        # Check if folder is in config.yaml
        if folder_path not in config.get("folders_to_embed", []):
            folder_statuses[folder_path] = "❌ Not Embedded"
        else:
            folder_statuses[folder_path] = "✅ Embedded"
    
    return folder_statuses

def selection_loop(selected_folders, folder_statuses, config):
    # Track newly selected folders and embed them
    newly_selected = set(selected_folders) - set(config.get("folders_to_embed", []))
    
    for folder in newly_selected:
        # Start embedding this folder (process it in the backend)
        embed_folder(folder)
        folder_statuses[folder] = "✅ Embedded"  # Update the status
    
    # Add to config.yaml
    config["folders_to_embed"].extend(newly_selected)
    save_config(config)
