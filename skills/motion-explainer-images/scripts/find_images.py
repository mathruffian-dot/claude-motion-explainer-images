"""Find and fetch freely licensed photos for a film from Wikimedia Commons (incl. NASA/PD images).

Only licences that allow reuse in a video are kept: public domain, CC0, CC BY, CC BY-SA.
(NC / ND / "fair use" files are dropped.) Every fetched file gets a CREDITS.md line with author,
licence and source URL — put that credit on screen next to the image.

  python find_images.py search "McMurtry Speirling" [--limit 8]
  python find_images.py get "File:2022 McMurtry Speirling.jpg" --name speirling --project <dir> [--width 1920]

`get` saves <project>/assets/images/web/<name>.<ext> and appends to assets/images/web/CREDITS.md.
Look at the image before using it (people, other brands' logos, watermarks) and crop accordingly.
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

API = "https://commons.wikimedia.org/w/api.php"
UA = "motion-explainer-images/1.0 (https://github.com/mathruffian-dot/claude-motion-explainer-images)"
OK = re.compile(r"^(public domain|pd\b|cc0|cc by(-sa)? \d|cc-by(-sa)?-\d)", re.I)


def api(params):
    params = {"format": "json", **params}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def info(page):
    ii = page["imageinfo"][0]
    m = ii.get("extmetadata", {})
    strip = lambda s: re.sub(r"<[^>]+>", "", s or "").strip()
    return {
        "title": page["title"],
        "width": ii.get("width"), "height": ii.get("height"),
        "license": strip(m.get("LicenseShortName", {}).get("value")),
        "license_url": strip(m.get("LicenseUrl", {}).get("value")),
        "artist": strip(m.get("Artist", {}).get("value"))[:80],
        "page": ii.get("descriptionurl"),
        "thumb": ii.get("thumburl"),
    }


def search(q, limit):
    d = api({"action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": q,
             "gsrlimit": limit * 3, "prop": "imageinfo", "iiprop": "url|size|extmetadata",
             "iiextmetadatafilter": "LicenseShortName|Artist"})
    rows = [info(p) for p in (d.get("query", {}).get("pages", {}) or {}).values()]
    rows = [r for r in rows if OK.match(r["license"] or "")][:limit]
    for r in rows:
        print(f'{r["title"][:72]:72} {r["width"]}x{r["height"]} | {r["license"]} | {r["artist"]}')
    if not rows:
        print("no freely licensed results — try other keywords, or generate an illustration instead")


def get(title, name, project, width):
    d = api({"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|size|extmetadata",
             "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist", "iiurlwidth": width})
    page = list(d["query"]["pages"].values())[0]
    if "imageinfo" not in page:
        sys.exit(f'no such file on Wikimedia Commons: {title} (copy the exact "File:..." title from search)')
    r = info(page)
    if not OK.match(r["license"] or ""):
        sys.exit(f'refusing {title}: licence "{r["license"]}" is not PD / CC0 / CC BY / CC BY-SA')
    ext = Path(urllib.parse.urlparse(r["thumb"]).path).suffix.lower() or ".jpg"
    dest_dir = Path(project).resolve() / "assets" / "images" / "web"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{name}{ext}"
    req = urllib.request.Request(r["thumb"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())
    credits = dest_dir / "CREDITS.md"
    lic = f'{r["license"]} ({r["license_url"]})' if r.get("license_url") else r["license"]
    line = (f'- {dest.name} — "{r["title"][5:]}" by {r["artist"] or "unknown"}, {lic}, via Wikimedia Commons: '
            f'{r["page"]} — modified for the film (cropped and resized; colour treatment as listed in media.json)\n')
    old = credits.read_text(encoding="utf-8") if credits.exists() else "# Image credits (web)\n\n"
    old = "".join(l for l in old.splitlines(keepends=True) if not l.startswith(f"- {dest.name} — "))  # re-fetch replaces
    credits.write_text(old + line, encoding="utf-8")
    print(f"saved {dest}")
    print(f'on-screen credit: Photo: {r["artist"] or "unknown"} · {r["license"]} · Wikimedia Commons')
    if "SA" in r["license"].upper():
        print("note: CC BY-SA — an edited (cropped/tinted) version stays under CC BY-SA; say so in the credits")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=8)
    g = sub.add_parser("get")
    g.add_argument("title")
    g.add_argument("--name", required=True)
    g.add_argument("--project", default=".")
    g.add_argument("--width", type=int, default=1920)
    a = ap.parse_args()
    if a.cmd == "search":
        search(a.query, a.limit)
    else:
        get(a.title, a.name, a.project, a.width)


if __name__ == "__main__":
    main()
