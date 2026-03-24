#!/usr/bin/env python3
"""
KDP Ebook Automation Pipeline
==============================
Uses Claude AI to generate a complete, ready-to-publish ebook for Amazon KDP.

Usage:
  python main.py "how to start a side hustle with no money"
  python main.py "intermittent fasting for beginners" --author "Jane Smith"
  python main.py "python for kids" --author "John Doe" --output ./my_ebooks
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from cover_gen import generate_cover
from epub_builder import build_epub
from generator import generate_chapter, generate_metadata, generate_outline


# ──────────────────────────────────────────────────────────────────────────────
# Upload instruction template
# ──────────────────────────────────────────────────────────────────────────────

_UPLOAD_TEMPLATE = """\
AMAZON KDP UPLOAD INSTRUCTIONS
================================
Generated : {now}

BOOK DETAILS
------------
Title    : {title}
Subtitle : {subtitle}
Author   : {author}

UPLOAD STEPS
------------
1. Go to https://kdp.amazon.com and sign in (or create a free account).

2. Click "Create" → "Kindle eBook".

3. KINDLE EBOOK DETAILS tab
   • Book title   : {title}
   • Subtitle     : {subtitle}
   • Author name  : {author}
   • Description  : (see kdp_metadata.json → "description")
   • Keywords     : (see kdp_metadata.json → "keywords") — enter up to 7
   • Categories   : (see kdp_metadata.json → "categories") — choose 2

4. KINDLE EBOOK CONTENT tab
   • Upload cover      : cover.jpg  (2560 × 1600 px — already correct)
   • Upload manuscript : {epub_name}
   • Enable "Enhanced typesetting" → YES

5. KINDLE EBOOK PRICING tab
   • Territories : All territories (worldwide)
   • Royalty plan: 70 % (requires list price $2.99–$9.99)
   • List price  : ${price_usd} USD
   • KDP Select  : optional (90-day exclusivity for extra promotions)

6. Click "Publish Your Kindle eBook".
   Review takes 24–72 hours; you'll get an email when it's live.

PASSIVE INCOME TIPS
-------------------
• Launch at $0.99 for the first week to collect reviews fast.
• Raise to $4.99–$9.99 once you have 10+ reviews.
• Run a free-day promotion every 90 days (KDP Select) to spike rankings.
• Spin up a paperback version (same content) for extra royalties — no extra writing.
• Reinvest in Amazon Ads using the keywords from kdp_metadata.json.
• Write a series: readers who buy one book often buy the rest.

FILES IN THIS PACKAGE
---------------------
{file_list}

HELP
----
KDP Help: https://kdp.amazon.com/en_US/help/topic/G200945180
"""


def _write_instructions(outline: dict, metadata: dict, out_path: Path, epub_name: str) -> None:
    file_list = "\n".join(f"  {f.name}" for f in sorted(out_path.iterdir()))
    text = _UPLOAD_TEMPLATE.format(
        now=datetime.now().strftime("%Y-%m-%d %H:%M"),
        title=outline["title"],
        subtitle=outline["subtitle"],
        author=outline.get("author_name", "Author"),
        epub_name=epub_name,
        price_usd=metadata.get("price_usd", 9.99),
        file_list=file_list,
    )
    (out_path / "UPLOAD_INSTRUCTIONS.txt").write_text(text)
    print("  ✓ UPLOAD_INSTRUCTIONS.txt written")


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────────────────────────────────────

def run_pipeline(topic: str, author_name: str, base_output: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(base_output) / f"ebook_{timestamp}"
    out_path.mkdir(parents=True, exist_ok=True)

    sep = "=" * 60
    print(f"\n{sep}")
    print("  KDP EBOOK AUTOMATION PIPELINE")
    print(sep)
    print(f"  Topic  : {topic}")
    print(f"  Author : {author_name}")
    print(f"  Output : {out_path}")
    print(f"{sep}\n")

    # ── Step 1: Outline ───────────────────────────────────────────────────────
    print("📋  Step 1 / 5 — Generating outline…")
    outline = generate_outline(topic)
    outline["author_name"] = author_name
    (out_path / "outline.json").write_text(json.dumps(outline, indent=2))
    print(f"  ✓ \"{outline['title']}\" — {len(outline['chapters'])} chapters\n")

    # ── Step 2: Chapters ──────────────────────────────────────────────────────
    print(f"📝  Step 2 / 5 — Writing {len(outline['chapters'])} chapters…\n")
    chapters_content: list[str] = []
    for ch in outline["chapters"]:
        print(f"  ─── Chapter {ch['number']}: {ch['title']} ───\n")
        content = generate_chapter(topic, ch, outline)
        chapters_content.append(content)
        (out_path / f"chapter_{ch['number']:02d}.md").write_text(content)
        print(f"\n  ✓ Chapter {ch['number']} saved\n")

    # ── Step 3: KDP Metadata ─────────────────────────────────────────────────
    print("🏷️   Step 3 / 5 — Generating KDP metadata…")
    metadata = generate_metadata(outline, topic)
    (out_path / "kdp_metadata.json").write_text(json.dumps(metadata, indent=2))
    print("  ✓ kdp_metadata.json written\n")

    # ── Step 4: Cover ─────────────────────────────────────────────────────────
    print("🎨  Step 4 / 5 — Creating cover image…")
    cover_path = out_path / "cover.jpg"
    generate_cover(
        title=outline["title"],
        subtitle=outline["subtitle"],
        author=author_name,
        output_path=cover_path,
    )
    print("  ✓ cover.jpg written (2560 × 1600 px)\n")

    # ── Step 5: EPUB ──────────────────────────────────────────────────────────
    print("📚  Step 5 / 5 — Building EPUB…")
    epub_path = build_epub(outline, chapters_content, cover_path, out_path)
    print(f"  ✓ {epub_path.name} written\n")

    # ── Upload instructions ───────────────────────────────────────────────────
    _write_instructions(outline, metadata, out_path, epub_path.name)

    print(f"{sep}")
    print("  ✅  PIPELINE COMPLETE")
    print(sep)
    print(f"\n  Output: {out_path}")
    print("\n  Files:")
    for f in sorted(out_path.iterdir()):
        size_kb = f.stat().st_size // 1024
        print(f"    {f.name:<45} {size_kb:>5} KB")
    print("\n  → Open UPLOAD_INSTRUCTIONS.txt for next steps.\n")

    return out_path


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a complete Amazon KDP ebook with Claude AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python main.py "how to start a side hustle with no money"\n'
            '  python main.py "intermittent fasting for beginners" --author "Jane Smith"\n'
            '  python main.py "python for kids" --author "John Doe" --output ./ebooks\n'
        ),
    )
    parser.add_argument("topic", help="Ebook topic or niche")
    parser.add_argument(
        "--author", default="Your Name", help="Author name (default: 'Your Name')"
    )
    parser.add_argument(
        "--output", default="output", help="Base output directory (default: output/)"
    )
    args = parser.parse_args()

    try:
        run_pipeline(args.topic, args.author, args.output)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
