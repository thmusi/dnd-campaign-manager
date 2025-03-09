import streamlit as st
import chromadb
import os
import json
import subprocess
import yaml
from pathlib import Path
import openai

CHROMA_DB_PATH = "chroma_db/"
CONFIG_FILE = "config.yaml"  # Now stored in your app's GitHub repo

# Load configuration from config.yaml
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    return {"obsidian_vault_path": "obsidian_vault", "folders_to_embed": []}

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
    """Lists modified files and allows manual selection for embedding."""
    last_update = load_last_update()
    updated_files = []

    for root, _, files in os.walk(OBSIDIAN_VAULT_PATH):
        if not any(folder in root for folder in FOLDERS_TO_EMBED):
            continue  # Skip files outside selected folders
        
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                last_modified = os.path.getmtime(file_path)
                if last_modified > last_update:
                    updated_files.append(file_path)

    if updated_files:
        st.subheader("📂 Select Files to Re-Embed")
        selected_files = st.multiselect("Choose files to embed:", updated_files)
        
        if st.button("🔄 Re-Embed Selected Files"):
            for file_path in selected_files:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    add_embedding(content, {"source": file_path})
            save_last_update()
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
