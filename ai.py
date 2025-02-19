import openai
import os

# Set up OpenAI client with API key
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  # Ensure API key is set in environment
)

def generate_npc():
    """Generates an NPC with stats, abilities, and spells."""
    response = client.chat.completions.create(
        model="gpt-4o",  # Update model if necessary
        messages=[
            {"role": "system", "content": "You are an expert D&D character generator."},
            {"role": "user", "content": "Generate a D&D NPC with a full stat block in French format."}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_location():
    """Generates a town, shop, or dungeon with details."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert D&D worldbuilder."},
            {"role": "user", "content": "Generate a detailed D&D town description with notable NPCs and shops."}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def modify_campaign_chapter(existing_text):
    """Modifies a campaign chapter to fit with past events."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a skilled D&D campaign editor."},
            {"role": "user", "content": f"Rewrite this chapter to match past events and world changes:\n\n{existing_text}"}
        ],
        temperature=0.6
    )
    return response.choices[0].message.content.strip()
