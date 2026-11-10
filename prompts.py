"""Prompt templates for the LinkedIn post generator."""

TONES = [
    "Professional",
    "Friendly",
    "Bold",
    "Inspirational",
    "Funny",
    "Storytelling",
]

LENGTHS = {
    "Short": "60-90 words",
    "Medium": "130-180 words",
    "Long": "220-300 words",
}

# Each variation uses a different angle so the three posts feel distinct.
ANGLES = [
    "personal story or lesson learned",
    "practical tips or how-to",
    "strong opinion or contrarian take",
]


def build_prompt(topic, tone, length, audience, angle):
    """Build one prompt for one variation of the post."""
    return f"""You are an expert LinkedIn ghostwriter.

Write one LinkedIn post with these details:
- Topic: {topic}
- Tone: {tone}
- Length: {LENGTHS[length]} (stay close to this word count)
- Audience: {audience}
- Creative angle: {angle}

Rules:
- Start with a strong first line that stops people from scrolling.
- Use short paragraphs with line breaks between them.
- Sound human and specific. Avoid corporate jargon.
- End with a question or a clear call to action.
- Add 3 to 5 relevant hashtags on the last line.
- Use plain text only. Do not use markdown symbols like ** or ##.
- Return only the post text. Do not add headings, labels, or explanations.
"""
