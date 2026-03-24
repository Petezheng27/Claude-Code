"""
Build a KDP-ready EPUB from generated content.
"""
from pathlib import Path

import markdown
from ebooklib import epub


_CSS = """
body {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.8;
  margin: 2em 1.5em;
  color: #222;
}
h1, h2, h3 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  color: #1a1a2e;
}
h1 { font-size: 2em; border-bottom: 2px solid #e8c547; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; margin-top: 2em; }
h3 { font-size: 1.2em; color: #16213e; }
p  { margin: 0.9em 0; text-align: justify; }
ul, ol { margin: 1em 0; padding-left: 2em; }
li { margin: 0.4em 0; }
strong { color: #1a1a2e; }
blockquote {
  border-left: 4px solid #e8c547;
  padding-left: 1em;
  font-style: italic;
  color: #555;
  margin: 1em 0;
}
"""


def _md_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["extra", "nl2br"])


def build_epub(
    outline: dict,
    chapters_content: list[str],
    cover_path: Path,
    output_dir: Path,
) -> Path:
    """Assemble and write the EPUB file; return its path."""
    book = epub.EpubBook()

    safe_title = outline["title"].replace(" ", "_").replace("/", "-")
    book.set_identifier(f"ebook-{safe_title.lower()}")
    book.set_title(outline["title"])
    book.set_language("en")
    book.add_author(outline.get("author_name", "Author"))

    # Stylesheet
    css_item = epub.EpubItem(
        uid="style_default",
        file_name="style/default.css",
        media_type="text/css",
        content=_CSS,
    )
    book.add_item(css_item)

    # Cover image
    if cover_path.exists():
        cover_data = cover_path.read_bytes()
        book.set_cover("cover.jpg", cover_data)

    # Title page
    title_page = epub.EpubHtml(title="Title Page", file_name="title.xhtml", lang="en")
    title_page.content = (
        "<html><body>"
        '<div style="text-align:center;padding:3em 1em;">'
        f'<h1 style="font-size:2.5em;border:none;">{outline["title"]}</h1>'
        f'<p style="font-size:1.2em;color:#555;font-style:italic;">{outline["subtitle"]}</p>'
        "<br/><br/>"
        f'<p style="color:#888;">by {outline.get("author_name","Author")}</p>'
        "</div>"
        "</body></html>"
    )
    title_page.add_item(css_item)
    book.add_item(title_page)

    # Chapters
    epub_chapters: list[epub.EpubHtml] = []
    toc_links: list[epub.Link] = []

    for chapter_info, content in zip(outline["chapters"], chapters_content):
        num = chapter_info["number"]
        chapter_title = f'Chapter {num}: {chapter_info["title"]}'
        html_body = _md_to_html(content)

        ch = epub.EpubHtml(
            title=chapter_title,
            file_name=f"chapter_{num:02d}.xhtml",
            lang="en",
        )
        ch.content = f"<html><body>{html_body}</body></html>"
        ch.add_item(css_item)
        book.add_item(ch)
        epub_chapters.append(ch)
        toc_links.append(epub.Link(ch.file_name, chapter_title, f"ch{num}"))

    book.toc = toc_links
    book.spine = ["nav", title_page] + epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output_path = output_dir / f"{safe_title}.epub"
    epub.write_epub(str(output_path), book, {})
    return output_path
