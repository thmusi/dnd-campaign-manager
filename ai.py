import openai
import os

def generate_npc(prompt="Generate a D&D NPC with a full stat block in French format"):
    """Generates an NPC with stats, abilities, and spells."""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert D&D character generator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )
    return response["choices"][0]["message"]["content"].strip()

def generate_location(prompt="Generate a detailed D&D town description with notable NPCs and shops"):
    """Generates a town, shop, or dungeon with details."""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert D&D worldbuilder."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"].strip()

def modify_campaign_chapter(existing_text, prompt="Rewrite this chapter to match past events and world changes"):
    """Modifies a campaign chapter to fit with past events."""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a skilled D&D campaign editor."},
            {"role": "user", "content": f"{prompt}\n\n{existing_text}"}
        ],
        temperature=0.6
    )
    return response["choices"][0]["message"]["content"].strip()

# Example Usage (For Testing)
if __name__ == "__main__":
    print("--- Generated NPC ---")
    print(generate_npc())
    print("\n--- Generated Location ---")
    print(generate_location())
