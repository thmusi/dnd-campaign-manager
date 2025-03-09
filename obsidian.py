import os
import json
from datetime import datetime
import streamlit as st
import re
import requests
        
def format_markdown_header(text):
    """Formats text as a Markdown header."""
    return f"# {text}\n"

        
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

