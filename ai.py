import openai
import streamlit as st
from embedding_management import retrieve_relevant_embeddings, chunk_text
from utils import summarize_text, chunk_text  # ✅ Fixed circular import


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
    
    return response.choices[0].message.content.strip()


# Define your templates for different query types
SPELL_TEMPLATE = """
**Spell Name**: {spell_name_fr_and_eng}
**Level**: {spell_level}
**Effect**: {spell_effect_fr_and_eng}
**Casting Time**: {casting_time}
**Components**: {components_fr_and_eng}
"""

CAMPAIGN_TEMPLATE = """
**Response**: {response}
"""

DEFAULT_TEMPLATE = """
**Response**: {response}
"""


# Function to generate AI response and apply templates
import openai
import streamlit as st
from embedding_management import retrieve_relevant_embeddings, chunk_text

def generate_ai_response(query, api_key, top_k=3, max_tokens=3000, query_type=None):
    """Generate AI response using relevant embeddings from ChromaDB and adapt based on query/page type."""
    
    retrieved_docs = retrieve_relevant_embeddings(query, top_k=top_k, max_tokens=max_tokens, query_type=query_type)
    context = "\n\n".join(retrieved_docs)

    # Handle chunking of context if it's too large
    context_chunks = chunk_text(context, max_tokens=max_tokens)

    client = openai.OpenAI(api_key=api_key)
    responses = []  # ✅ Ensure this list is inside the function

    for chunk in context_chunks:  # ✅ Ensure this is inside the function
        if query_type == "/s":  
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI assistant providing bilingual (French/English) D&D spell details."},
                    {"role": "user", "content": f"Provide this spell's details in both French and English: {query}\n\nContext:\n{chunk}"}
                ]
            )
            spell_data = response.choices[0].message.content.strip()
            formatted_response = SPELL_TEMPLATE.format(
                spell_name_fr_and_eng=query,
                spell_level="3",
                spell_effect_fr_and_eng=spell_data,
                casting_time="1 action",
                components_fr_and_eng="V, S"
            )

        elif query_type == "/c":  
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI assistant for D&D campaigns."},
                    {"role": "user", "content": f"Answer this campaign-related query: {query}\n\nContext:\n{chunk}"}
                ]
            )
            campaign_data = response.choices[0].message.content.strip()
            formatted_response = CAMPAIGN_TEMPLATE.format(response=campaign_data)

        elif query_type == "/r":  
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI assistant for D&D 5e rules."},
                    {"role": "user", "content": f"Answer this DnD 5e Rules query: {query}\n\nContext:\n{chunk}"}
                ]
            )
            rules_data = response.choices[0].message.content.strip()
            formatted_response = DEFAULT_TEMPLATE.format(response=rules_data)  # ✅ Fixed

        else:  
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI assistant."},
                    {"role": "user", "content": f"Answer this query: {query}\n\nContext:\n{chunk}"}
                ]
            )
            default_data = response.choices[0].message.content.strip()
            formatted_response = DEFAULT_TEMPLATE.format(response=default_data)

        responses.append(formatted_response)  # ✅ Ensure this is inside the function

    return " ".join(responses)  # ✅ Ensure this is inside the function


# Add the context to existing functions (e.g., NPC, Shop, Location)
def generate_npc(api_key, occupation, query_type="generate_npc"):
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
  - **Niveau Y (Y = niveau de sort disponible en fonction du niveau du personnage/NPJ) (X/Repos Long) :** [Liste] 

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
    return generate_ai_response(prompt, api_key, query_type=query_type)

def generate_shop(api_key, shop_type="General Store", custom_prompt=None, query_type="/c"):
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
    return generate_ai_response(prompt, api_key, query_type=query_type)

def generate_location(api_key, location_prompt=None, query_type="/c"):
    prompt = f"Crée un lieu immersif pour une campagne D&D en respectant les règles de la 5e édition. {location_prompt if location_prompt else ''}"
    return generate_ai_response(prompt, api_key, query_type=query_type)


