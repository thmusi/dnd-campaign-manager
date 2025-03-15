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
import ast

CHROMA_DB_PATH = "chroma_db"
MODIFICATION_TRACKER = "modification_tracker.yaml"
VAULT_PATH = "obsidian_vault"


def load_config():
    db = chromadb.PersistentClient(path="chroma_db")
    collection = db.get_or_create_collection("campaign_notes")

    # Fetch stored config
    result = collection.get(ids=["folders_to_embed"])

    # Ensure the result contains valid data
    if result and "documents" in result and result["documents"]:
        stored_config = result["documents"][0]  # Retrieve stored value

        if isinstance(stored_config, str):
            try:
                stored_config = ast.literal_eval(stored_config)  # Safe way to convert string to dictionary
            except (SyntaxError, ValueError):
                stored_config = {}  # Reset if conversion fails

        if isinstance(stored_config, dict):
            return stored_config  # ✅ Return parsed config if valid

    return {"obsidian_vault_path": "obsidian_vault", "folders_to_embed": []}  # Default config


def save_config(config):
    db = chromadb.PersistentClient(path="chroma_db")
    collection = db.get_or_create_collection("campaign_notes")
    collection.upsert(
        ids=["folders_to_embed"],
        documents=[str(config)]  # Store as string to avoid format issues
    )

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


# ✅ Initialize OpenAI embeddings
import streamlit as st

def get_openai_embedding_function():
    """Fetch OpenAI API key from session state and initialize the embedding function."""
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction  # ✅ Import inside the function

    api_key = st.session_state.get("openai_api_key", None)
    
    if not api_key:
        raise ValueError("❌ OpenAI API key not found. Please enter it on the API Key page.")

    return OpenAIEmbeddingFunction(api_key=api_key)

# ✅ Initialize embedding function dynamically
embedding_function = None  # Initialize as None to avoid errors before the API key is set

# ✅ Check if Streamlit session is active before setting it
if "openai_api_key" in st.session_state:
    embedding_function = get_openai_embedding_function()

MAX_TOKENS = 8000  # Safe token limit for embedding

def embed_selected_folders(folders_to_embed, vault_path=VAULT_PATH):
    """
    Embeds selected folders into ChromaDB and ensures embeddings are stored correctly.
    """
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = db.get_or_create_collection(name="campaign_notes")

    for folder in folders_to_embed:
        full_folder_path = os.path.join(vault_path, folder)

        if not os.path.exists(full_folder_path):
            print(f"⚠️ Folder does not exist: {full_folder_path}")
            continue

        for root, _, files in os.walk(full_folder_path):
            for file in files:
                file_path = os.path.join(root, file)

                # ✅ Fetch existing document metadata safely
                existing_docs = collection.get(ids=[file_path])
                metadata_list = existing_docs.get("metadatas", [])

                metadata = metadata_list[0] if metadata_list and isinstance(metadata_list[0], dict) else {}
                filename = metadata.get("filename", file_path)  # Use file path if filename is missing

                # ✅ Debugging: Print metadata safely
                print(f"📌 Document: {filename} (Metadata Found: {bool(metadata)})")

                # ✅ Read file content
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except Exception as e:
                    print(f"❌ Error reading {file_path}: {e}")
                    continue

                # ✅ Check if content exists
                if not content.strip():
                    print(f"⚠️ Skipping empty file: {file_path}")
                    continue

                # ✅ Embed document
                try:
                    collection.upsert(
                        ids=[file_path],
                        documents=[content],
                        metadatas=[{"source_folder": folder, "filename": filename}]
                    )
                    print(f"✅ Successfully embedded: {file_path}")
                except Exception as e:
                    print(f"❌ Error embedding {file_path}: {e}")

    print("🔄 Finished embedding process.")

# Function to list stored embeddings
def list_embeddings():
    docs = collection.get()
    return docs if docs else {"ids": [], "documents": []}


# Function to manually add an embedding
import subprocess

def add_embedding_and_push(vault_path="obsidian_vault", chroma_db_path="chroma_db"):
    """
    Pushes ChromaDB embeddings to GitHub.
    """
    try:
        # Ensure ChromaDB has valid embeddings before pushing
        embedding_file = os.path.join(chroma_db_path, "chroma.sqlite3")
        if not os.path.exists(embedding_file):
            print("❌ No embeddings found in ChromaDB. Skipping push.")
            return
        
        # GitHub Operations
        repo_path = os.path.join(vault_path, ".git")
        if not os.path.exists(repo_path):
            print("⚠️ Vault is not a Git repository. Cloning again...")
            subprocess.run(["rm", "-rf", vault_path])  # Remove old folder
            subprocess.run(["git", "clone", "GITHUB_REPO_URL", vault_path])  # Clone fresh copy
            subprocess.run(["git", "config", "--global", "user.email", "theoesperet@gmail.com"])
            subprocess.run(["git", "config", "--global", "user.name", "thmusi"])

        os.chdir(vault_path)
        subprocess.run(["git", "pull"])  # Ensure latest updates

        # ✅ Instead of embeddings.json, push chroma_db/
        subprocess.run(["git", "add", chroma_db_path])
        subprocess.run(["git", "commit", "-m", "Updated embeddings in ChromaDB"])
        subprocess.run(["git", "push"])

        os.chdir("..")  # Return to previous directory

        print("✅ ChromaDB embeddings added and pushed to GitHub successfully!")

    except Exception as e:
        print(f"❌ Error handling embeddings: {e}")

# Function to retrieve relevant embeddings
from utils import summarize_text, chunk_text

def retrieve_relevant_embeddings(query, top_k=3, max_tokens=3000, query_type=None):
    """Retrieve relevant embeddings with weighted folder importance and apply chunking & summarization if needed."""
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = db.get_or_create_collection("campaign_notes")

    folder_weights = {
        "/s": {"Rulebooks/Spells": 3},
        "/c": {"A. Campaign": 2, "C. Inspiration": 2, "B. Exandria": 1},
        "/r": {"Rulebooks": 3},
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

    # ✅ Debug: Print stored document filenames BEFORE querying
    stored_docs = collection.get(include=["metadatas"])
    print("📂 Checking stored document file paths BEFORE retrieval...")
    for idx, metadata in enumerate(stored_docs.get("metadatas", [])):
        if metadata:
            print(f"📌 Stored Document {idx+1}: {metadata.get('filename', 'UNKNOWN')}")
        else:
            print(f"⚠️ Warning: Metadata missing for document {idx+1}")

    # ✅ Run the query
    results = collection.query(query_texts=[query], n_results=top_k * 2)

    # ✅ Print raw retrieved results
    print("🔍 Raw Retrieved Documents:")
    for idx, doc in enumerate(results.get("documents", [])):
        print(f"📌 Result {idx+1} (Unfiltered):\n{doc[:300]}\n")  # Print first 300 characters

    # ✅ Exclude "folders_to_embed" and invalid results
    valid_results = []
    for doc, metadata_list in zip(results.get("documents", []), results.get("metadatas", [])):
        if metadata_list and isinstance(metadata_list, list) and metadata_list:
            metadata = metadata_list[0]  # ✅ Ensure metadata is not None
            if not isinstance(metadata, dict):
                metadata = {}  # ✅ Fallback to an empty dict

            if metadata.get("filename") != "folders_to_embed":
                valid_results.append((doc, metadata))
        else:
            print(f"⚠️ Warning: Skipping document due to missing metadata.")

    # ✅ Print valid results
    print("✅ Valid Retrieved Documents AFTER Filtering:")
    for idx, (doc, metadata) in enumerate(valid_results[:top_k]):
        print(f"📌 Result {idx+1}: {metadata.get('filename', 'UNKNOWN')}\n🔎 Content Preview:\n{doc[:300]}\n")

    # ✅ Prepare final sorted & chunked response
    sorted_docs = [doc if isinstance(doc, str) else "\n".join(doc) for doc, _ in valid_results[:top_k]]
    combined_text = "\n\n".join(sorted_docs)
    
    # ✅ Ensure text fits within max token limit
    if len(combined_text.split()) > max_tokens:
        combined_text = summarize_text(combined_text, max_tokens=max_tokens // 2)

    final_docs = chunk_text(combined_text, max_tokens=max_tokens)

    return final_docs

def remove_embedding(folders_to_remove, vault_path=OBSIDIAN_VAULT_PATH):
    """
    Removes embeddings from ChromaDB.
    """
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = db.get_or_create_collection(name="campaign_notes")

    removed_files = []
    stored_results = collection.get()  # Fetch all stored data once
    stored_ids = set(stored_results.get("ids", []))  # Get stored document IDs

    for folder in folders_to_remove:
        full_folder_path = os.path.join(vault_path, folder)

        if os.path.exists(full_folder_path):
            for root, _, files in os.walk(full_folder_path):
                for file in files:
                    file_path = os.path.join(root, file)

                    # ✅ Check if file exists in ChromaDB by exact match
                    if file_path in stored_ids:
                        collection.delete(ids=[file_path])
                        removed_files.append(file_path)
                        print(f"❌ Removed embedding: {file_path}")
                    else:
                        print(f"⚠️ File not found in embeddings: {file_path}")

    if removed_files:
        print("✅ Successfully removed embeddings from ChromaDB.")
    else:
        print("⚠️ No embeddings were removed.")

def update_config_yaml_after_removal(removed_files, config_path="config.yaml"):
    """
    Updates config.yaml after removing embeddings.
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

        config["embedded_files"] = [f for f in config.get("embedded_files", []) if f not in removed_files]

        with open(config_path, "w") as f:
            yaml.dump(config, f)

        print("✅ Updated config.yaml after removing embeddings.")

    except Exception as e:
        print(f"❌ Error updating config.yaml: {e}")

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
    """Lists all markdown and PDF files per folder and allows manual selection for embedding."""
    
    if not FOLDERS_TO_EMBED:
        st.info("No folders are selected for embedding. Choose folders in the Folder Embedding Management page.")
        return
    
    for folder in FOLDERS_TO_EMBED:  # Iterate over selected folders
        full_folder_path = os.path.join(OBSIDIAN_VAULT_PATH, folder)
        
        updated_files = []
        for root, _, files in os.walk(full_folder_path):
            for file in files:
                if file.endswith((".md", ".pdf", ".json")):  # Include PDFs & JSON
                    updated_files.append(os.path.join(root, file))
        
        if updated_files:
            st.subheader(f"📂 {folder} - Select Files to Re-Embed")
            
            selected_files = st.multiselect(
                f"Choose files to embed in {folder}:",  # Use folder name dynamically
                updated_files, 
                key=f"multiselect_{folder}"  # Ensure a unique key per folder
            )

            if selected_files and st.button(f"🔄 Re-Embed Selected Files in {folder}", key=f"reembed_{folder}"):
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

                st.success(f"✅ Re-embedded {len(selected_files)} files in {folder}!")
        else:
            st.info(f"📁 No modified files detected in {folder}.")


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
    """Load stored selected folders from ChromaDB."""
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = db.get_or_create_collection("campaign_notes")

    try:
        result = collection.get(ids=["selected_folders"])
        if result and "documents" in result and result["documents"]:
            stored_folders = json.loads(result["documents"][0])  # Convert back to list
            print(f"✅ Loaded selected folders: {stored_folders}")  # Debugging
            return set(stored_folders)
    except Exception as e:
        print(f"❌ Error loading selected folders: {e}")

    return set()  # Return empty set if nothing found


def save_selected_folders(folders):
    """Save the selected folders persistently to ChromaDB instead of config.yaml."""
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = db.get_or_create_collection("campaign_notes")

    # Store selected folders in ChromaDB
    collection.upsert(
        ids=["selected_folders"],
        documents=[json.dumps(list(folders))],  # Store as JSON string
    )

    print(f"✅ Saved selected folders: {folders}")  # Debugging
def reset_folder_status_on_pull(all_folders, config):
    # Initialize all folders as "Not Embedded" if not in config.yaml
    folder_statuses = {}
    
    for folder_path, _, _ in all_folders:
        # Check if folder is in config.yaml
        if folder_path not in load_config().get("folders_to_embed", []):
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
    new_config = load_config()
    new_config["folders_to_embed"].extend(newly_selected)
    save_config(new_config)
