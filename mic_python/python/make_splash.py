# make_splash.py - generates splash.png for the PyInstaller one-file splash
# (dev-only: requires Pillow, which is NOT needed at runtime)
#
# The splash is painted by the PyInstaller bootloader BEFORE python starts,
# covering the one-file self-extraction window on cold starts.

from PIL import Image, ImageDraw, ImageFont

W, H = 480, 240
BG = (6, 10, 6)
GREEN = (138, 255, 90)
DIM = (95, 115, 95)

ART = [
    "TALKER",
]

def load_font(size):
    for name in ("consola.ttf", "lucon.ttf", "cour.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_font = load_font(72)
    sub_font = load_font(18)

    # centered title with a subtle double shadow for LCD depth
    bbox = d.textbbox((0, 0), "TALKER", font=title_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = (W - tw) // 2, (H - th) // 2 - 18
    d.text((x + 3, y + 3), "TALKER", font=title_font, fill=(29, 51, 22))
    d.text((x, y), "TALKER", font=title_font, fill=GREEN)

    sub = "PDA booting..."
    bbox = d.textbbox((0, 0), sub, font=sub_font)
    sw = bbox[2] - bbox[0]
    d.text(((W - sw) // 2, y + th + 28), sub, font=sub_font, fill=DIM)

    img.save("splash.png")
    print("splash.png written", img.size)


if __name__ == "__main__":
    main()
