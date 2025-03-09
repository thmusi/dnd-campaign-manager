import os
import json
from datetime import datetime
import streamlit as st
import re
import requests
        

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

