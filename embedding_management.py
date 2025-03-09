import streamlit as st
import chromadb
import os
import json
from pathlib import Path
import openai

CHROMA_DB_PATH = "chroma_db/"

# Ensure directory exists and persist embeddings
if not os.path.exists(CHROMA_DB_PATH):
    os.makedirs(CHROMA_DB_PATH)

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

# Streamlit Page Rendering
