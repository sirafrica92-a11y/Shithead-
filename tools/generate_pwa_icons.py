"""Generate Android/PWA icons from the existing, owner-approved jester logo.

Run from anywhere after installing Pillow:
    python -m pip install Pillow==12.0.0
    python tools/generate_pwa_icons.py

Outputs are deterministic display copies, never replacements for the source.
No network, API keys, generated branding, or gameplay code.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "server" / "app" / "static" / "brand"
SOURCE = BRAND / "shithead-logo.png"
ICON_192 = BRAND / "shithead-logo-192.png"
MASKABLE_512 = BRAND / "shithead-maskable-512.png"

def main():
    with Image.open(SOURCE) as source:
        if source.size != (512, 512):
            raise ValueError(f"Expected original 512px square logo, got {source.size}")
        logo = source.convert("RGBA")

    # Properly sized PWA launcher icon; never mislabel the existing 180px image.
    logo.resize((192, 192), Image.Resampling.LANCZOS).save(
        ICON_192, format="PNG", optimize=True
    )

    # Keep all card corners within the circular Android maskable safe area.
    background = Image.new("RGB", (512, 512), "#0b0b0e")
    centered = logo.resize((284, 284), Image.Resampling.LANCZOS)
    background.paste(centered, (114, 114), centered)
    background.save(MASKABLE_512, format="PNG", optimize=True)

    for item, expected in ((ICON_192, (192,192)), (MASKABLE_512, (512,512))):
        with Image.open(item) as check:
            if check.size != expected:
                raise AssertionError(f"{item.name}: expected {expected}, got {check.size}")
        print(f"{item.relative_to(ROOT)}: {expected[0]}x{expected[1]}")

if __name__ == "__main__":
    main()
