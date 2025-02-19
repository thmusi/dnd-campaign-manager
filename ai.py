import openai

def generate_npc(api_key, prompt=None):
    """Generates an NPC with an optional prompt for customization."""
    client = openai.OpenAI(api_key=api_key)  # Initialize OpenAI client
    messages = [
        {"role": "system", "content": "You are an expert D&D character generator."},
        {"role": "user", "content": prompt if prompt else "Generate a D&D NPC with a full stat block in French format."}
    ]
    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    return response.choices[0].message.content.strip()

def generate_location(api_key, prompt=None):
    """Generates a town, shop, or dungeon with optional customization."""
    client = openai.OpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": "You are an expert D&D worldbuilder."},
        {"role": "user", "content": prompt if prompt else "Generate a detailed D&D town description with notable NPCs and shops."}
    ]
    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    return response.choices[0].message.content.strip()

def modify_campaign_chapter(existing_text, api_key, prompt=None):
    """Modifies a campaign chapter with optional custom changes."""
    client = openai.OpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": "You are a skilled D&D campaign editor."},
        {"role": "user", "content": f"{prompt if prompt else 'Rewrite this chapter to match past events and world changes:'}\n\n{existing_text}"}
    ]
    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    return response.choices[0].message.content.strip()
