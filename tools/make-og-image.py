#!/usr/bin/env python3
"""Generate the 1200x630 Open Graph image for docs.pytest.org.

Pillow-only, reproducible. Run from the repo root:
    python tools/make-og-image.py
Output: doc/en/_static/og-image.png

Design: white ground, the project's own pytest1.png logo scaled on top,
official tagline, section pills, docs.pytest.org domain chip.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "doc" / "en" / "_static" / "pytest1.png"
OUT = ROOT / "doc" / "en" / "_static" / "og-image.png"

W, H = 1200, 630
GROUND = (255, 255, 255)
ACCENT = (250, 179, 14)      # pytest yellow
INK = (34, 34, 34)
GREY = (110, 110, 110)
PILL_BG = (245, 245, 245)
PILL_FG = (51, 51, 51)
CHIP_BG = (250, 179, 14)
CHIP_FG = (34, 34, 34)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu/")
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_REG = FONT_DIR / "DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(str(path), size)


def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def main():
    img = Image.new("RGB", (W, H), GROUND)
    draw = ImageDraw.Draw(img)

    # Accent bar along the top.
    draw.rectangle([0, 0, W, 10], fill=ACCENT)

    # Logo: the project's own pytest1.png (1500x1500, transparent bg, contains
    # the bar-chart mark + "pytest" wordmark). Scale to fit fully on the card.
    logo = Image.open(LOGO).convert("RGBA")
    logo_w = 400
    logo_h = int(logo.height * logo_w / logo.width)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
    img.paste(logo, ((W - logo_w) // 2, 15), logo)

    # Tagline.
    tagline = "helps you write better programs"
    f_tag = font(FONT_REG, 40)
    draw.text(((W - text_w(draw, tagline, f_tag)) / 2, 430), tagline,
              font=f_tag, fill=GREY)

    # Section pills.
    pills = ["Getting started", "How-to guides", "Reference", "Explanations", "Examples"]
    f_pill = font(FONT_BOLD, 26)
    gap = 16
    pw = [text_w(draw, p, f_pill) + 40 for p in pills]
    total = sum(pw) + gap * (len(pills) - 1)
    x = (W - total) / 2
    for p, wdt in zip(pills, pw):
        draw.rounded_rectangle([x, 485, x + wdt, 485 + 52], radius=26, fill=PILL_BG)
        draw.text((x + 20, 485 + 11), p, font=f_pill, fill=PILL_FG)
        x += wdt + gap

    # Domain chip.
    chip = "docs.pytest.org"
    f_chip = font(FONT_BOLD, 30)
    cw = text_w(draw, chip, f_chip) + 56
    cx = (W - cw) / 2
    cy = 555
    draw.rounded_rectangle([cx, cy, cx + cw, cy + 56], radius=28, fill=CHIP_BG)
    draw.text((cx + 28, cy + 11), chip, font=f_chip, fill=CHIP_FG)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"wrote {OUT} {img.size}")


if __name__ == "__main__":
    main()