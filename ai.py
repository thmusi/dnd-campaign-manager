import openai
from obsidian import upload_to_obsidian  # Import Dropbox function
from obsidian import write_note  # Ensure this is present at the top


def save_ai_generated_content(file_name, content):
    """Uploads AI-generated content to the Obsidian vault on Dropbox."""
    return upload_to_obsidian(file_name, content)

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
- **Sorts mineurs (utilisation illimitée) :**
  - [Liste]
- **Sorts à emplacements (X/Repos Long) :**
  - **Niveau 1 (X/Repos Long) :** [Liste] 
  - **Niveau 2 (X/Repos Long) :** [Liste] 
  - **Niveau 3 (X/Repos Long) :** [Liste] 
  - **Niveau X (X = niveau de sort disponible en fonction du niveau du personnage/NPJ) (X/Repos Long) :** [Liste] 

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

    npc_content = response.choices[0].message.content.strip()

    if not npc_content:
        return "❌ AI failed to generate NPC."

    markdown_content = f"# {occupation}\n\n{npc_content}"
    
    success = write_note(f"NPC_{occupation.replace(' ', '_')}.md", markdown_content)
    
    if success:
        print(f"✅ NPC '{occupation}' saved to Obsidian via Dropbox.")
    else:
        print("❌ Failed to save NPC to Dropbox.")
    
    return npc_content

def generate_shop(api_key, shop_type="General Store", custom_prompt=None):
    """Generates a detailed D&D shop description, including inventory, owner, security measures, and lore."""

    # List of allowed shop types
    allowed_shop_types = [
        "General Store", "Blacksmith", "Alchemy Shop", "Magic Shop", "Tavern",
        "Jewelry Store", "Weapon Shop", "Armorer", "Fletcher", "Tailor", "Enchanter"
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
    - Ajoute **une ou plusieurs particularités visibles et concrètes du magasin** (ex: un comptoir avec des marques profondes comme si quelqu'un y avait frappé un énorme poing, une vitrine avec une seule place vide et une étiquette indiquant "Réservé", des marchandises étiquetées dans une langue inconnue).
    - Décris **une interaction directe possible avec cet élément** (ex: si les joueurs demandent ce qu’il y avait sur la place vide de la vitrine, le propriétaire change de sujet, ou une personne entre soudainement et se met en colère de voir l’étagère toujours vide).
    - Donne **une explication logique et utilisable en jeu** que le propriétaire peut fournir **(ou refuser de donner avec une raison claire)** (ex: "Cette marque sur le comptoir ? Un géant en colère voulait un remboursement.").
    - Fournis **un élément exploitable pour le MJ** (ex: si un joueur touche une arme spécifique, le propriétaire les observe plus attentivement, ou leur propose immédiatement un travail).

        ### 🔍 **Explication pour le MJ** :
        - Décrit **ce qui est réellement en train de se passer** derrière cette particularité du magasin.
        - Explique **l’origine ou la cause** (ex: pourquoi cette vitrine est toujours vide, pourquoi l’enclume runique brille).
        - Indique **les effets concrets en jeu**, si les joueurs interagissent avec cet élément.


    ## 🔐 **Mesures de sécurité et réactions en cas de vol** :
    - Précise **les protections contre le vol** (runes magiques, golems de garde, sorts...) et, si applicable, en décrivant les jets de sauvegarde nécessaire et les dégats.
    - Décris **comment le propriétaire réagirait** si un vol était tenté.

    {f"- Instructions spécifiques : {custom_prompt}" if custom_prompt else ""}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    shop_content = response.choices[0].message.content.strip()

    if not shop_content:
        return "❌ AI failed to generate Shop."

    markdown_content = f"# {shop_type}\n\n{shop_content}"

    success = write_note(f"Shop_{shop_type.replace(' ', '_')}.md", markdown_content)
    
    if success:
        print(f"✅ Shop '{shop_type}' saved to Obsidian via Dropbox.")
    else:
        print("❌ Failed to save Shop to Dropbox.")

    return shop_content

def generate_location(api_key, prompt=None):
    client = openai.OpenAI(api_key=api_key)

    ai_prompt = "Crée un lieu immersif pour une campagne D&D en respectant les règles de la 5e édition."
    if prompt:
        ai_prompt += f" {prompt}"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": ai_prompt}]
    )

    location_content = response.choices[0].message.content.strip()

    if not location_content:
        return "❌ AI failed to generate Location."

    markdown_content = f"# Location\n\n{location_content}"
    
    success = write_note("Location_Generated.md", markdown_content)
    
    return location_content if success else "❌ Failed to save Location."



def modify_campaign_chapter(existing_text, api_key, prompt=None):
    """Modifies a campaign chapter with optional custom changes."""
    client = openai.OpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": "You are a skilled D&D campaign editor."},
        {"role": "user", "content": f"{prompt if prompt else 'Rewrite this chapter to match past events and world changes:'}\n\n{existing_text}"}
    ]
    response = client.chat.completions.create(model="gpt-4o", messages=messages)

    # Save modified chapter to Dropbox (Obsidian) with correct Markdown formatting
    campaign_content = response.choices[0].message.content.strip()
    markdown_content = f"# Modified Chapter\n\n{campaign_content}"
    obsidian.write_note("Modified_Campaign_Chapter.md", markdown_content)
    print("✅ Modified campaign chapter saved to Obsidian via Dropbox.")

    return response.choices[0].message.content.strip()


