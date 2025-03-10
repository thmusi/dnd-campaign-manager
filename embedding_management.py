import streamlit as st
import chromadb
import os
import json
import subprocess
import yaml
from pathlib import Path
import openai
import pandas as pd


CHROMA_DB_PATH = "chroma_db/"
CONFIG_FILE = "config.yaml"  # Now stored in your app's GitHub repo
CONFIG_PATH = "config.yaml"

# Load configuration from config.yaml
def load_config():
    try:
        with open(CONFIG_PATH, "r") as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}  # Return empty config if file is missing
    except yaml.YAMLError:
        st.error("⚠️ Error reading config.yaml. Check file format.")
        return {}

def save_config(config):
    with open(CONFIG_PATH, "w") as file:
        yaml.safe_dump(config, file)

config = load_config()
OBSIDIAN_VAULT_PATH = config["obsidian_vault_path"]
FOLDERS_TO_EMBED = set(config["folders_to_embed"])

# Ensure necessary directories exist
if not os.path.exists(CHROMA_DB_PATH):
    os.makedirs(CHROMA_DB_PATH)
if not os.path.exists(OBSIDIAN_VAULT_PATH):
    os.makedirs(OBSIDIAN_VAULT_PATH)

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_or_create_collection(name="campaign_notes")

# Function to list stored embeddings
def list_embeddings():
    docs = collection.get()
    return docs if docs else {"ids": [], "documents": []}

# Function to remove an embedding
def remove_embedding(embedding_id):
    collection.delete(ids=[embedding_id])
    st.success(f"✅ Removed embedding {embedding_id}")

# Function to manually add an embedding
def add_embedding(text, metadata):
    embedding_id = f"doc_{len(list_embeddings()['ids']) + 1}"
    if not metadata:
        metadata = {"source": "manual"}  # Ensure metadata is a valid dictionary
    collection.add(ids=[embedding_id], documents=[text], metadatas=[metadata])
    st.success("✅ Added embedding successfully!")

# Function to retrieve relevant embeddings
def retrieve_relevant_embeddings(query, top_k=3):
    """Search ChromaDB for relevant embeddings based on a user query."""
    results = collection.query(query_texts=[query], n_results=top_k)
    retrieved_docs = results.get("documents", [])
    
    # Ensure retrieved_docs is a flat list of strings
    flattened_docs = [item for sublist in retrieved_docs for item in (sublist if isinstance(sublist, list) else [sublist])]
    
    return flattened_docs if flattened_docs else []

# Function to generate AI response with retrieved context
def generate_ai_response(query, api_key):
    """Generate an AI response using relevant embeddings from ChromaDB."""
    retrieved_docs = retrieve_relevant_embeddings(query)
    context = "\n\n".join(retrieved_docs) if retrieved_docs else "No relevant data found."
    
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AI assistant for a D&D campaign."},
            {"role": "user", "content": f"Based on the following campaign notes, answer this question: {query}\n\nContext:\n{context}"}
        ]
    )
    
    return response.choices[0].message.content.strip()

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
    """Lists all markdown files and allows manual selection for embedding."""
    updated_files = []

    for root, _, files in os.walk(OBSIDIAN_VAULT_PATH):
        # If folders_to_embed is empty, allow all files
        if FOLDERS_TO_EMBED and not any(folder in root for folder in FOLDERS_TO_EMBED):
            continue  

        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                updated_files.append(file_path)

    if updated_files:
        st.subheader("📂 Select Files to Re-Embed")
        selected_files = st.multiselect("Choose files to embed:", updated_files)

        if st.button("🔄 Re-Embed Selected Files"):
            for file_path in selected_files:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
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
    
    for root, dirs, _ in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith(".git")]  # Exclude .git folders
        rel_path = os.path.relpath(root, base_path)
        parts = rel_path.split(os.sep) if rel_path != '.' else []
        node = folder_tree
        for part in parts:
            node = node.setdefault(part, {})
    
    st.write("📂 Debug: Folder Structure", folder_tree)  # Debugging output
    return folder_tree
    
def get_subfolders(tree, path):
    """Returns the subfolder dictionary at a given path."""
    node = tree
    for part in path.split("/"):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node
