"""Place treated images into built frames: evidence cards and full-bleed backgrounds.

Reads "placements" from images.json and injects, into each target frame:
  - an absolutely positioned element (card or background) inside the composition root
  - a <script> that appends its entrance tween to the frame's registered GSAP timeline
Idempotent: a previous injection (between the PLACE markers) is replaced on every run, so run it
after theme.py (theme.py restores pre-theme copies and would drop the injection) and before
subset_fonts.py (captions/credits add characters).

images.json "placements": [
  {"frame": "03-suction", "image": "speirling", "mode": "card",
   "box": [640, 96, 540, 351], "at": 12.0,
   "label": "前例：McMurtry Spéirling 風扇吸地車（2022）",
   "credit": "Photo: Calreyn88 · CC BY-SA 4.0 · Wikimedia Commons"},
  {"frame": "01-hook", "image": "hook-loop", "mode": "background", "after": "01-hook-bg",
   "opacity": 0.42, "at": 0.0, "credit": "AI 生成示意圖"}
]
box = [x, y, w, h] of the image in canvas px (the card's label sits under it).
  python place_images.py --project <dir>
"""
import sys
import argparse
import json
import re
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

START, END = "<!-- PLACE:start -->", "<!-- PLACE:end -->"
JS_START, JS_END = "<!-- PLACE-JS:start -->", "<!-- PLACE-JS:end -->"


def strip_previous(t):
    t = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", t, flags=re.S)
    return re.sub(re.escape(JS_START) + r".*?" + re.escape(JS_END) + r"\n?", "", t, flags=re.S)


def element(p, k, theme):
    pid = f"{p['frame']}-place-{k}"
    src = f"assets/images/treated/{p['image']}.jpg"
    fg, bg = theme["fg"], theme["bg"]
    fam = (theme.get("font") or {}).get("family")  # theme.json "font" wins, like all other text
    LABEL = (f"\'{fam}\'," if fam else "") + "\'Hanken Grotesk\',\'NotoSansTC\',sans-serif"
    MONO = (f"\'{fam}\'," if fam else "") + "\'DM Mono\',\'NotoSansTC\',monospace"
    if p["mode"] == "background":
        style = (f"position:absolute;inset:0;z-index:0;opacity:0;"
                 f"background:url('{src}') center/cover no-repeat;")
        credit = ""
        if p.get("credit"):
            credit = (f'<div style="position:absolute;right:80px;top:72px;font:500 15px {MONO};'
                      f'letter-spacing:0.06em;color:{fg};opacity:0.7;">{p["credit"]}</div>')
        return pid, f'<div id="{pid}" style="{style}">{credit}</div>'
    x, y, w, h = p["box"]
    label = p.get("label", "")
    credit = p.get("credit", "")
    if p.get("label_side") == "right":
        tw = p.get("text_width", 420)
        return pid, (
            f'<div id="{pid}" style="position:absolute;left:{x}px;top:{y}px;display:flex;gap:22px;align-items:flex-end;z-index:40;opacity:0;">'
            f'<div style="flex:none;width:{w}px;height:{h}px;border:2px solid {fg};background:{bg} url(\'{src}\') center/cover no-repeat;"></div>'
            f'<div style="width:{tw}px;padding-bottom:4px;">'
            f'<div style="font:600 22px {LABEL};color:{fg};line-height:1.35;">{label}</div>'
            f'<div style="margin-top:8px;font:400 14px {MONO};letter-spacing:0.04em;color:{fg};opacity:0.72;line-height:1.4;">{credit}</div>'
            f"</div></div>")
    html = (
        f'<div id="{pid}" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;z-index:40;opacity:0;">'
        f'<div style="width:{w}px;height:{h}px;border:2px solid {fg};background:{bg} url(\'{src}\') center/cover no-repeat;"></div>'
        f'<div style="margin-top:10px;font:600 21px {LABEL};color:{fg};line-height:1.3;">{label}</div>'
        f'<div style="margin-top:4px;font:400 14px {MONO};letter-spacing:0.04em;color:{fg};opacity:0.72;">{credit}</div>'
        f"</div>"
    )
    return pid, html


def tween(p, pid):
    at = float(p.get("at", 0))
    # "hide": ids of drawn elements the image replaces (e.g. a line-art car under a photo of a car)
    hide_at = float(p.get("hide_at", at))
    hide = "".join(
        f'(function(e){{if(e)tl.fromTo(e,{{opacity:1}},{{opacity:0,duration:0.6,ease:"power2.in"}},{hide_at});}})'
        f'(document.getElementById("{h}"));' for h in p.get("hide", []))
    if p["mode"] == "background":
        op = p.get("opacity", 0.4)
        return hide + (f'tl.fromTo(document.getElementById("{pid}"), {{opacity:0}}, '
                       f'{{opacity:{op}, duration:0.9, ease:"power2.out"}}, {at});')
    return hide + (f'tl.fromTo(document.getElementById("{pid}"), {{opacity:0, y:24, clipPath:"inset(0 100% 0 0)"}}, '
                   f'{{opacity:1, y:0, clipPath:"inset(0 0% 0 0)", duration:0.8, ease:"expo.out"}}, {at});')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    theme = json.loads((project / "theme.json").read_text(encoding="utf-8"))
    spec = json.loads((project / "images.json").read_text(encoding="utf-8"))
    by_frame = {}
    for k, p in enumerate(spec.get("placements", [])):
        by_frame.setdefault(p["frame"], []).append((k, p))
    for f in sorted((project / "compositions" / "frames").glob("*.html")):
        t = strip_previous(f.read_text(encoding="utf-8"))
        items = by_frame.get(f.stem, [])
        if items:
            els, tws = [], []
            for k, p in items:
                pid, html = element(p, k, theme)
                els.append((p, html))
                tws.append(tween(p, pid))
            for p, html in els:
                block = f"{START}\n{html}\n{END}\n"
                if p["mode"] == "background" and p.get("after"):
                    m = re.search(rf'<div[^>]*id="{re.escape(p["after"])}"[^>]*>(?:\s*</div>)?', t)
                    assert m, f"{f.name}: anchor #{p['after']} not found"
                    t = t[:m.end()] + "\n" + block + t[m.end():]
                else:
                    m = re.search(r'<div[^>]*id="root"[^>]*>', t)
                    assert m, f"{f.name}: composition root not found"
                    t = t[:m.end()] + "\n" + block + t[m.end():]
            js = (f'{JS_START}\n<script>(function(){{var tl=window.__timelines["{f.stem}"];'
                  f'if(!tl)return;{"".join(tws)}}})();</script>\n{JS_END}\n')
            i = t.rindex("</template>")
            t = t[:i] + js + t[i:]
        f.write_text(t, encoding="utf-8")
        if items:
            print("placed", len(items), "image(s) in", f.name)


if __name__ == "__main__":
    main()
