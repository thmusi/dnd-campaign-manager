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

def generate_shop(api_key, shop_type="General Store", custom_prompt=None):
    """Generates a detailed D&D shop description, including inventory, owner, security measures, and lore."""

    # List of allowed shop types
    allowed_shop_types = [
        "General Store", "Blacksmith", "Alchemy Shop", "Magic Shop", "Tavern",
        "Jewelry Store", "Weapon Shop", "Armorer", "Fletcher"
    ]

    # Validate shop type
    if shop_type not in allowed_shop_types:
        return f"❌ Erreur : Le type de boutique '{shop_type}' n'est pas valide. Choisissez parmi {', '.join(allowed_shop_types)}."

    client = openai.OpenAI(api_key=api_key)

    prompt = f"""
    Crée une boutique immersive pour une campagne D&D en respectant les règles de la 5e édition.
    Décris les éléments suivants :

    **📜 Nom du magasin** : Choisis un nom unique et thématique en fonction du type de boutique ({shop_type}).

    **👤 Propriétaire** : Décris son nom, sa race et sa personnalité.

    🗣️ **Description à lire aux joueurs :**
    "Un texte immersif que le MJ peut lire à voix haute, décrivant l'apparence, le comportement et l'aura générale du PNJ lorsqu'il est rencontré par les joueurs."

    ## 🛍️ **Inventaire Principal (D&D 5e)** :
    - Liste **5 à 10 objets**, incluant des **objets magiques et non magiques** correspondant au type de boutique ({shop_type}).
    - Utilise les objets **officiels de D&D 5e** et inclut leurs **prix standards**.
    - Pour chaque objet, fournis **une description détaillée**, en précisant ses effets et caractéristiques.

   ## 🔎 **Ce qui rend ce magasin intéressant** :
    - Choisis **un élément étrange, une caractéristique unique ou une anomalie** propre à cette boutique (ex: une horloge sans aiguilles qui fonctionne malgré tout, un client qui semble toujours être là quelle que soit l'heure de la journée, un objet qui apparaît différemment selon la personne qui le regarde).
    - Décris **comment les joueurs le remarquent immédiatement** (ex: une sensation de déjà-vu, une ombre qui ne correspond pas, une impression de murmure à la limite de l’audible).
    - Fournis **une explication plausible ou mystérieuse** donnée par le propriétaire (ex: "C'est un vieux mécanisme elfique" ou "Personne ne sait vraiment pourquoi, mais cela ne semble pas dangereux...").
    - Ajoute **une conséquence possible en jeu** si les joueurs interagissent avec cet élément (ex: l'objet leur murmure un secret, la boutique semble légèrement changer à leur prochaine visite, le propriétaire leur demande de ne plus poser de questions).

    ## 🔐 **Mesures de sécurité et réactions en cas de vol** :
    - Précise **les protections contre le vol** (runes magiques, golems de garde, sorts...) et, si applicable, en décrivant les jets de sauvegarde nécessaire et les dégats.
    - Décris **comment le propriétaire réagirait** si un vol était tenté.

    {f"- Instructions spécifiques : {custom_prompt}" if custom_prompt else ""}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
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

