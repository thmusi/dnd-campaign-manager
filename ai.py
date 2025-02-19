import openai
import os

# Ensure API key is set
client = openai.OpenAI(api_key=os.getenv("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"))

def generate_npc():
    """Generates an NPC with stats, abilities, and spells."""
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert D&D character generator."},
            {"role": "user", "content": "Generate a D&D NPC with a full stat block in French format."}
        ]
    )
    return response.choices[0].message.content.strip()

def generate_location():
    """Generates a town, shop, or dungeon with details."""
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert D&D worldbuilder."},
            {"role": "user", "content": "Generate a detailed D&D town description with notable NPCs and shops."}
        ]
    )
    return response.choices[0].message.content.strip()

def modify_campaign_chapter(existing_text):
    """Modifies a campaign chapter to fit with past events."""
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a skilled D&D campaign editor."},
            {"role": "user", "content": f"Rewrite this chapter to match past events and world changes:\n\n{existing_text}"}
        ]
    )
    return response.choices[0].message.content.strip()

