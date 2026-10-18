"""Fit photos and generated images to the film's three-color theme.

images.json (project root):
{
  "speirling": {"src": "assets/images/web/speirling.jpg", "crop": [x0, y0, x1, y1],
                "mode": "duotone", "size": [1600, 1000]},
  "hook-loop": {"src": "assets/images/gen/hook-loop.png", "mode": "keep", "darken": 0.85}
}
modes:
  duotone — grayscale, then shadows -> theme bg, highlights -> theme fg (photos from the web:
            they join the palette and leave the accent color to the film's key points)
  keep    — keep the colors (images generated on-theme), optional darken factor
Writes assets/images/treated/<name>.jpg.   python treat_images.py --project <dir>
"""
import sys
import argparse
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    theme = json.loads((project / "theme.json").read_text(encoding="utf-8"))
    spec = json.loads((project / "images.json").read_text(encoding="utf-8"))
    out_dir = project / "assets" / "images" / "treated"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, s in spec.items():
        if name.startswith("_") or not isinstance(s, dict) or "src" not in s:
            continue
        im = Image.open(project / s["src"]).convert("RGB")
        if s.get("crop"):
            im = im.crop(tuple(s["crop"]))
        if s.get("size"):
            im = ImageOps.fit(im, tuple(s["size"]), Image.LANCZOS)
        if s.get("mode", "duotone") == "duotone":
            g = ImageOps.autocontrast(im.convert("L"), cutoff=1)
            g = ImageEnhance.Contrast(g).enhance(s.get("contrast", 1.15))
            im = ImageOps.colorize(g, black=hex_rgb(theme["bg"]), white=hex_rgb(theme["fg"]))
        if s.get("darken"):
            im = ImageEnhance.Brightness(im).enhance(s["darken"])
        dest = out_dir / f"{name}.jpg"
        im.save(dest, quality=88)
        print(f"{name}: {im.size[0]}x{im.size[1]} -> {dest.relative_to(project)}")


if __name__ == "__main__":
    main()
