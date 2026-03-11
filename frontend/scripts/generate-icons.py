#!/usr/bin/env python3
"""
Generate PWA icons from source SVG.
Requires: pip install cairosvg pillow
"""

import os
from pathlib import Path

try:
    import cairosvg
    from PIL import Image
    from io import BytesIO
except ImportError:
    print("Please install dependencies: pip install cairosvg pillow")
    exit(1)

SCRIPT_DIR = Path(__file__).parent
PUBLIC_DIR = SCRIPT_DIR.parent / "public"
ICONS_DIR = PUBLIC_DIR / "icons"
SPLASH_DIR = PUBLIC_DIR / "splash"

SVG_SOURCE = ICONS_DIR / "icon.svg"

ICON_SIZES = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]

MASKABLE_SIZES = [192, 512]

SPLASH_SCREENS = [
    (2048, 2732, "apple-splash-2048-2732.png"),  # iPad Pro 12.9"
    (1668, 2388, "apple-splash-1668-2388.png"),  # iPad Pro 11"
    (1290, 2796, "apple-splash-1290-2796.png"),  # iPhone 14 Pro Max
    (1179, 2556, "apple-splash-1179-2556.png"),  # iPhone 14 Pro
    (1170, 2532, "apple-splash-1170-2532.png"),  # iPhone 14
]

def svg_to_png(svg_path: Path, size: int, output_path: Path):
    """Convert SVG to PNG at specified size."""
    png_data = cairosvg.svg2png(
        url=str(svg_path),
        output_width=size,
        output_height=size,
    )
    with open(output_path, "wb") as f:
        f.write(png_data)
    print(f"Generated: {output_path.name} ({size}x{size})")

def create_maskable_icon(svg_path: Path, size: int, output_path: Path):
    """Create maskable icon with safe zone padding."""
    inner_size = int(size * 0.8)
    padding = (size - inner_size) // 2

    png_data = cairosvg.svg2png(
        url=str(svg_path),
        output_width=inner_size,
        output_height=inner_size,
    )

    inner_img = Image.open(BytesIO(png_data))
    final_img = Image.new("RGBA", (size, size), (14, 165, 233, 255))
    final_img.paste(inner_img, (padding, padding), inner_img)
    final_img.save(output_path, "PNG")
    print(f"Generated: {output_path.name} (maskable {size}x{size})")

def create_splash_screen(svg_path: Path, width: int, height: int, output_path: Path):
    """Create splash screen with centered icon."""
    icon_size = min(width, height) // 4
    png_data = cairosvg.svg2png(
        url=str(svg_path),
        output_width=icon_size,
        output_height=icon_size,
    )

    icon_img = Image.open(BytesIO(png_data))
    splash_img = Image.new("RGBA", (width, height), (15, 23, 42, 255))
    x = (width - icon_size) // 2
    y = (height - icon_size) // 2
    splash_img.paste(icon_img, (x, y), icon_img)
    splash_img.save(output_path, "PNG")
    print(f"Generated: {output_path.name} ({width}x{height})")

def main():
    if not SVG_SOURCE.exists():
        print(f"Error: SVG source not found at {SVG_SOURCE}")
        exit(1)

    ICONS_DIR.mkdir(exist_ok=True)
    SPLASH_DIR.mkdir(exist_ok=True)

    for size in ICON_SIZES:
        output = ICONS_DIR / f"icon-{size}x{size}.png"
        svg_to_png(SVG_SOURCE, size, output)

    apple_touch = ICONS_DIR / "apple-touch-icon.png"
    svg_to_png(SVG_SOURCE, 180, apple_touch)

    for size in MASKABLE_SIZES:
        output = ICONS_DIR / f"icon-maskable-{size}x{size}.png"
        create_maskable_icon(SVG_SOURCE, size, output)

    shortcut_plan = ICONS_DIR / "shortcut-plan.png"
    shortcut_chat = ICONS_DIR / "shortcut-chat.png"
    svg_to_png(SVG_SOURCE, 96, shortcut_plan)
    svg_to_png(SVG_SOURCE, 96, shortcut_chat)

    for width, height, filename in SPLASH_SCREENS:
        output = SPLASH_DIR / filename
        create_splash_screen(SVG_SOURCE, width, height, output)

    print("\nAll icons generated successfully!")
    print(f"Icons: {ICONS_DIR}")
    print(f"Splash screens: {SPLASH_DIR}")

if __name__ == "__main__":
    main()
