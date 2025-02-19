import openai
import os

# Ensure API key is properly set
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_npc():
    """Generates an NPC with stats, abilities, and spells."""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert D&D character generator."},
            {"role": "user", "content": "Generate a D&D NPC with a full stat block in French format."}
        ]
    )
    return response["choices"][0]["message"]["content"].strip()

def generate_location():
    """Generates a town, shop, or dungeon with details."""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert D&D worldbuilder."},
            {"role": "user", "content": "Generate a detailed D&D town description with notable NPCs and shops."}
        ]
    )
    return response["choices"][0]["message"]["content"].strip()

def modify_campaign_chapter(existing_text):
    """Modifies a campaign chapter to fit with past events."""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a skilled D&D campaign editor."},
            {"role": "user", "content": f"Rewrite this chapter to match past events and world changes:\n\n{existing_text}"}
        ]
    )
    return response["choices"][0]["message"]["content"].strip()
