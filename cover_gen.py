"""
Generate a professional-looking KDP book cover using Pillow.
KDP recommended dimensions: 2560 × 1600 px (portrait for ebooks: 2560 h × 1600 w).
"""
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# KDP ebook cover: height > width (portrait)
COVER_W, COVER_H = 1600, 2560

# Colour palette
BG_TOP    = (15, 25, 55)
BG_BOTTOM = (5, 10, 30)
ACCENT    = (232, 197, 71)   # gold
TITLE_FG  = (255, 255, 255)
SUB_FG    = ACCENT
AUTHOR_FG = (180, 180, 200)

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _find_font(size: int) -> ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """Break *text* into lines that fit within *max_width* pixels."""
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        try:
            w = draw.textbbox((0, 0), candidate, font=font)[2]
        except Exception:
            w = len(candidate) * (font.size if hasattr(font, "size") else 20)
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines or [text]


def _draw_centered(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.ImageFont,
    y: int,
    colour: tuple,
    line_gap: int,
    width: int,
) -> int:
    """Draw centred text lines starting at *y*; return the new y position."""
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
        except Exception:
            lw = len(line) * (font.size if hasattr(font, "size") else 20)
        x = (width - lw) // 2
        # subtle drop shadow
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=colour)
        y += line_gap
    return y


def generate_cover(
    title: str,
    subtitle: str,
    author: str,
    output_path: Path,
) -> Path:
    """Render a cover image and save it as JPEG."""
    img = Image.new("RGB", (COVER_W, COVER_H))
    draw = ImageDraw.Draw(img)

    # Vertical gradient background
    for y in range(COVER_H):
        t = y / COVER_H
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (COVER_W, y)], fill=(r, g, b))

    margin = 80

    # Top accent lines
    draw.rectangle([margin, 190, COVER_W - margin, 198], fill=ACCENT)
    draw.rectangle([margin, 202, COVER_W - margin, 206], fill=(255, 255, 255, 80))

    # Bottom accent lines
    draw.rectangle([margin, COVER_H - 206, COVER_W - margin, COVER_H - 202], fill=(255, 255, 255, 80))
    draw.rectangle([margin, COVER_H - 198, COVER_W - margin, COVER_H - 190], fill=ACCENT)

    max_text_w = COVER_W - margin * 2

    # Title
    title_font = _find_font(110)
    title_lines = _wrap_text(draw, title.upper(), title_font, max_text_w)
    title_y = 280
    title_y = _draw_centered(draw, title_lines, title_font, title_y, TITLE_FG, 130, COVER_W)

    # Divider
    title_y += 40
    draw.rectangle([margin + 200, title_y, COVER_W - margin - 200, title_y + 3], fill=ACCENT)
    title_y += 30

    # Subtitle
    if subtitle:
        sub_font = _find_font(58)
        sub_lines = _wrap_text(draw, subtitle, sub_font, max_text_w)
        title_y += 20
        _draw_centered(draw, sub_lines, sub_font, title_y, SUB_FG, 75, COVER_W)

    # Author (pinned near bottom)
    author_font = _find_font(52)
    author_lines = _wrap_text(draw, author, author_font, max_text_w)
    author_y = COVER_H - 160 - len(author_lines) * 65
    _draw_centered(draw, author_lines, author_font, author_y, AUTHOR_FG, 65, COVER_W)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "JPEG", quality=95)
    return output_path
