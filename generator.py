"""
Claude-powered content generation for KDP ebooks.
"""
import json
import anthropic

client = anthropic.Anthropic()


def _parse_json_response(text: str) -> dict:
    """Parse JSON from Claude response, stripping markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Drop opening fence and optional language tag
        start = 1
        if lines[start].strip().lower() in ("json", ""):
            start += 1
        # Drop closing fence
        end = len(lines)
        while end > start and lines[end - 1].strip() == "```":
            end -= 1
        text = "\n".join(lines[start:end])
    return json.loads(text.strip())


def generate_outline(topic: str) -> dict:
    """Generate a full book outline for the given topic."""
    print("  Calling Claude to plan the outline…")
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=(
            "You are an expert ebook author and Amazon KDP publishing strategist. "
            "Create compelling, high-value ebook outlines that sell well. "
            "Focus on practical, actionable content readers will pay for."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f'Create a detailed outline for an ebook on: "{topic}"\n\n'
                    "Return ONLY a JSON object — no prose, no code fences:\n"
                    "{\n"
                    '  "title": "Compelling Book Title",\n'
                    '  "subtitle": "Descriptive Subtitle That Sells",\n'
                    '  "chapters": [\n'
                    "    {\n"
                    '      "number": 1,\n'
                    '      "title": "Chapter Title",\n'
                    '      "description": "What this chapter covers",\n'
                    '      "key_points": ["point 1", "point 2", "point 3"]\n'
                    "    }\n"
                    "  ],\n"
                    '  "target_audience": "Description of ideal reader",\n'
                    '  "word_count_target": 15000\n'
                    "}\n\n"
                    "Include 8-12 chapters covering a complete transformation for the reader."
                ),
            }
        ],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return _parse_json_response(text)


def generate_chapter(topic: str, chapter: dict, outline: dict) -> str:
    """Stream a full chapter and return the complete text."""
    parts: list[str] = []
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        system=(
            "You are an expert author writing practical, engaging ebook content. "
            "Use a clear, conversational style. Include real examples and actionable advice. "
            "Format with markdown headings (## for chapter title, ### for subheadings), "
            "paragraphs, bullet lists, and **bold** for key terms."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f'Write Chapter {chapter["number"]}: "{chapter["title"]}" '
                    f'for the ebook "{outline["title"]}".\n\n'
                    f'Book subtitle: {outline["subtitle"]}\n'
                    f'Target audience: {outline["target_audience"]}\n\n'
                    f'Chapter description: {chapter["description"]}\n'
                    f'Key points to cover: {", ".join(chapter["key_points"])}\n\n'
                    "Write approximately 1,500–2,000 words. "
                    "Start directly with the chapter content — no preamble."
                ),
            }
        ],
    ) as stream:
        for delta in stream.text_stream:
            parts.append(delta)
            print(delta, end="", flush=True)
    print()
    return "".join(parts)


def generate_metadata(outline: dict, topic: str) -> dict:
    """Generate Amazon KDP-optimised metadata."""
    print("  Calling Claude to craft KDP metadata…")
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        thinking={"type": "adaptive"},
        system=(
            "You are an Amazon KDP publishing expert who specialises in "
            "metadata optimisation for maximum discoverability and sales."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Create optimised Amazon KDP metadata for:\n"
                    f"Title: {outline['title']}\n"
                    f"Subtitle: {outline['subtitle']}\n"
                    f"Topic: {topic}\n"
                    f"Audience: {outline['target_audience']}\n\n"
                    "Return ONLY a JSON object — no prose, no code fences:\n"
                    "{\n"
                    '  "title": "...",\n'
                    '  "subtitle": "...",\n'
                    '  "description": "HTML-formatted sales copy (400-4000 chars) using <p><b><ul><li>",\n'
                    '  "keywords": ["kw1","kw2","kw3","kw4","kw5","kw6","kw7"],\n'
                    '  "categories": [\n'
                    '    {"browse_path": "Kindle Store > Kindle eBooks > Category > Subcategory"}\n'
                    "  ],\n"
                    '  "language": "English",\n'
                    '  "price_usd": 9.99\n'
                    "}\n\n"
                    "Pick keywords Amazon customers actually search for. "
                    "Make the description compelling sales copy."
                ),
            }
        ],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return _parse_json_response(text)
