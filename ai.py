import openai

def generate_npc(api_key):
    """Generates an NPC with stats, abilities, and spells."""
    client = openai.OpenAI(api_key=api_key)  # Initialize OpenAI client
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert D&D character generator."},
            {"role": "user", "content": "Generate a D&D NPC with a full stat block in French format."}
        ]
    )
    return response.choices[0].message.content.strip()

def generate_location(api_key):
    """Generates a town, shop, or dungeon with details."""
    client = openai.OpenAI(api_key=api_key)  # Initialize OpenAI client
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert D&D worldbuilder."},
            {"role": "user", "content": "Generate a detailed D&D town description with notable NPCs and shops."}
        ]
    )
    return response.choices[0].message.content.strip()

def modify_campaign_chapter(existing_text, api_key):
    """Modifies a campaign chapter to fit with past events."""
    client = openai.OpenAI(api_key=api_key)  # Initialize OpenAI client
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a skilled D&D campaign editor."},
            {"role": "user", "content": f"Rewrite this chapter to match past events and world changes:\n\n{existing_text}"}
        ]
    )
    return response.choices[0].message.content.strip()
