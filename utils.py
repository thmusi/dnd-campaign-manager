import openai

# Summarize text (if too long, useful for large documents)
def summarize_text(text, max_tokens=3000):
    """Summarizes long text to fit within the token limit."""
    prompt = f"Summarize the following text:\n{text}"
    response = openai.Completion.create(
        model="gpt-4o",
        prompt=prompt,
        max_tokens=max_tokens
    )
    return response.choices[0].text.strip()


# Chunk text into smaller pieces if it exceeds token limits
def chunk_text(text, max_tokens=3000):
    """Splits text into smaller chunks of manageable size."""
    chunks = []
    while len(text) > max_tokens:
        # Find the last space within the max token length
        split_point = text.rfind(" ", 0, max_tokens)
        chunks.append(text[:split_point])
        text = text[split_point:].strip()
    chunks.append(text)  # Append the final chunk
    return chunks
