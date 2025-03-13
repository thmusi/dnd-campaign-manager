import openai

# Summarize text (if too long, useful for large documents)
def summarize_text(text, max_tokens=3000):
    """Summarizes long text to fit within the token limit."""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Summarize the following text."},
                  {"role": "user", "content": text}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


def chunk_text(text, max_tokens=3000):
    """Splits text into smaller chunks of manageable size."""
    chunks = []
    while len(text) > max_tokens:
        split_point = text.rfind(" ", 0, max_tokens)
        chunks.append(text[:split_point])
        text = text[split_point:].strip()
    chunks.append(text)  # Append the final chunk
    return chunks
