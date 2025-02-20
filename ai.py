import openai

def generate_npc(api_key, occupation):
    client = openai.OpenAI(api_key=api_key)

    prompt = f"""
    Crée un PNJ détaillé pour une campagne D&D en respectant les règles de la 5e édition.
    Adapte sa classe en fonction de son occupation : {occupation}. Si la classe n'est pas naturellement magique, ne lui attribue pas de sorts.

    🛡️ **PNJ Généré**

    **Nom** : [Généré]
    **Race** : [Générée selon l’univers]
    **Classe** : [Adaptée selon l’occupation]
    **Niveau** : [Approprié]

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

    🏅 **Capacités et Traits :**
    - [Capacités spéciales liées à la classe et au niveau]
    - [Traits raciaux spécifiques]
    - [Talents ou capacités uniques du PNJ]

    🔥 **Sorts connus / Attaques connues (en fonction de la / des classes du NPC) :**

    **Sorts (si applicable, uniquement pour classes magiques) :**
    - **Sorts mineurs :**
      - [Liste]
    - **Niveau 1 ou plus :**
      - [Liste] (X / Repos Long ou Repos Court selon la classe)

    **Attaques (si applicable) :**
    - Armes ou autres (précision) +X : XdX dégâts de (type de dégâts)

    ⚔️ **Équipement et objets magiques :**
    - [Armures, objets notables, objets magiques (si applicable)]

    🎭 **Personnalité et rôle dans l’univers :**
    - **Caractère et motivations** : [Traits, ambitions et croyances]
    - **Phrase typique ou tic de langage** : [Exemple]
    - **Secrets et conflits internes** : [Élément caché intéressant pour les joueurs]

    📜 **Histoire et importance en jeu :**
    - **Biographie courte** : [Son passé]
    - **Lien avec la campagne** : [Pourquoi les joueurs pourraient l’approcher]

    🗣️ **Description à lire aux joueurs :**
    "Un texte immersif que le MJ peut lire à voix haute, décrivant l'apparence, le comportement et l'aura générale du PNJ lorsqu'il est rencontré par les joueurs."
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def generate_shop(api_key, shop_type, prompt=None):
    """Generates a detailed D&D shop description including inventory, owner, and special items."""
    client = openai.OpenAI(api_key=api_key)

    shop_prompt = f"""
    Crée une boutique détaillée pour une campagne D&D en fonction du type de boutique : {shop_type}.
    Décris les éléments suivants :
    - **Nom du magasin** (créatif et immersif)
    - **Propriétaire** (Nom, race, personnalité, secrets cachés)
    - **Inventaire principal** (articles courants et spéciaux)
    - **Atmosphère et disposition du magasin**
    - **Prix et marchandage** (prix typiques, possibilités de réduction)
    - **Rumeurs et interactions possibles avec les joueurs**
    {f"- Instructions supplémentaires : {prompt}" if prompt else ""}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": shop_prompt}]
    )

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

