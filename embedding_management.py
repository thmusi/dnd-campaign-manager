import os
import yaml
import chromadb

# Initialize ChromaDB Persistent Client
db = chromadb.PersistentClient(path="chroma_db/")
collection = db.get_or_create_collection("campaign_notes")

# Load config file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

vault_path = config["obsidian_vault_path"]
folders_to_embed = config["folders_to_embed"]

print("Configured folders to embed:", folders_to_embed)

# Embedding loop 💅
for folder in folders_to_embed:
    full_path = os.path.join(vault_path, folder)
    print(f"👠 Checking folder: {full_path}")

    if not os.path.exists(full_path):
        print(f"❌ Folder NOT found: {full_path}")
        continue

    for file in os.listdir(full_path):
        file_path = os.path.join(full_path, file)
        print(f"🔥 Preparing to embed: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if content:
            collection.add(
                documents=[content],
                ids=[file_path]
            )
            print("✅ Successfully added document to ChromaDB!")
        else:
            print(f"⚠️ File empty, skipping: {file_path}")

print(f"🎀 Total documents embedded: {collection.count()}")
