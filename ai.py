import openai

def generate_npc(api_key, occupation):
    client = openai.OpenAI(api_key=api_key)

    prompt = f"""
    Crée un PNJ détaillé pour une campagne D&D en respectant les règles de la 5e édition.
    Adapte sa classe en fonction de son occupation : {occupation}. Mélange deux classes ou crée une nouvelle classe si nécessaire, en respectant les mécaniques D&D 5E.

    🛡️ **PNJ Généré**

    **Nom** : [Généré]
    **Race** : [Générée selon l’univers]
    **Classe** : [Adaptée selon l’occupation]
    **Niveau** : [Approprié]
    **Alignement** : [Généré selon la personnalité]

    🛡️ **Statistiques :**

    | Statistique | Valeur | Modificateur |
    |------------|--------|-------------|
    | **FOR**    | X      | X           |
    | **DEX**    | X      | X           |
    | **CON**    | X      | X           |
    | **INT**    | X      | X           |
    | **SAG**    | X      | X           |
    | **CHA**    | X      | X           |

    📖 **Compétences & Modificateurs :**

    | Compétence et Modificateur | Compétence et Modificateur | Compétence et Modificateur |
    |---------------------------|---------------------------|---------------------------|
    | Acrobaties (DEX) : X     | Arcanes (INT) : X        | Athlétisme (FOR) : X     |
    | Discrétion (DEX) : X     | Dressage (SAG) : X       | Escamotage (DEX) : X     |
    | Histoire (INT) : X       | Intimidation (CHA) : X   | Investigation (INT) : X  |
    | Médecine (SAG) : X       | Nature (INT) : X        | Perception (SAG) : X     |
    | Persuasion (CHA) : X     | Religion (INT) : X      | Représentation (CHA) : X |
    | Supercherie (CHA) : X    | Survie (SAG) : X        |                           |

    📖 **Capacités & Traits Spéciaux :**
    - [Compétences uniques, talents raciaux, et capacités de classe]
    - [Pouvoirs spéciaux ou capacités de homebrew si pertinent]

    🔥 **Sorts connus (si applicable) :**

    **Sorts mineurs :**
    - [Liste]

    **Niveau 1 :**
    - [Liste]

    **Niveau 2+ :**
    - [Liste adaptée au niveau du PNJ]
    - **Recharges** : Déterminer si les sorts se récupèrent par **repos court** ou **repos long** en fonction du niveau et de la classe du PNJ.

    ⚔️ **Équipement et objets magiques :**
    - [Armes, armures, objets notables]

    🎭 **Personnalité et rôle dans l’univers :**
    - **Caractère et motivations** : [Traits, ambitions et croyances]
    - **Phrase typique ou tic de langage** : [Exemple]
    - **Secrets et conflits internes** : [Élément caché intéressant pour les joueurs]

    📜 **Histoire et importance en jeu :**
    - **Biographie courte** : [Son passé]
    - **Lien avec la campagne** : [Pourquoi les joueurs pourraient l’approcher]
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

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
