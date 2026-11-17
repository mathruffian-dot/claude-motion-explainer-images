"""Generate illustration images through the local Codex CLI's imagegen skill (built-in image_gen).

gen_prompts.json (project root):
{
  "_style": "Woodcut print illustration, warm ink on aged paper, bold carved lines.",   (optional)
  "hook-loop":  "Cinematic wide 16:9 photo-illustration. A sleek unbranded electric hypercar ...",
  "hero-sheet": "Full-body costume sheet of the main character ...",
  "hero-tavern": {"prompt": "The same man standing at a tavern counter ...",
                  "refs": ["assets/images/gen/hero-sheet.png"]}
}
- A value is a prompt string, or an object with "prompt", optional "refs" (image paths relative to the
  project, attached to that image's run so a character keeps the same face, clothes and drawing
  style) and optional "style" (overrides "_style" for that image).
- "_style" sets the look for every image. Without it the old default is used:
  "Photoreal, high contrast, sharp." — leave it out only when photoreal is what you want.
- Every prompt also gets the guard rails: no logos/badges/text/real brands, plus the theme's
  background and accent colours from theme.json.
Images land in <project>/assets/images/gen/<name>.png. Label them 「AI 生成示意圖」 on screen.
Images without refs go in one Codex run; each image with refs gets its own run, after the others,
in file order — so a ref can be an image generated earlier in the same call (e.g. a costume sheet).

  python codex_images.py --project <dir> [--only hook-loop] [--dry-run]

Requires the Codex CLI (`codex`) signed in; the built-in image_gen tool needs no OPENAI_API_KEY.
Runs `codex exec -` with the task on stdin (an open, empty stdin would make it wait forever; a long
argument is mangled by codex.cmd on Windows).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
sys.stdout.reconfigure(errors="replace")  # never crash printing Chinese or accented names on a non-UTF-8 console

GUARD = ("Completely unbranded: no logos, no badges, no emblems, no text or lettering anywhere, "
         "not any real brand's design.")
DEFAULT_STYLE = "Photoreal, high contrast, sharp."
REF_NOTE = ("Use the attached reference image(s) for this image: keep the same character identity "
            "(face, hair, build), the same clothes and props, and the same drawing style and palette. "
            "Do not copy their composition or pose unless the prompt asks for it.")


def run_codex(task, out_dir, refs, effort, log_name):
    codex = shutil.which("codex")  # on Windows this resolves codex.cmd, which a bare "codex" would not
    if not codex:
        sys.exit("codex CLI not found — install it, or generate the images another way into assets/images/gen/")
    cmd = [codex, "exec", "--skip-git-repo-check", "-s", "workspace-write",
           "-c", f"model_reasoning_effort={effort}"]
    for r in refs:
        cmd += ["-i", str(r)]
    with open(out_dir / log_name, "w", encoding="utf-8") as log:
        # the task goes in on stdin ("-"): a multi-line argument is mangled by codex.cmd on Windows,
        # and an open stdin with no input would make codex wait forever
        subprocess.run(cmd + ["-"], cwd=out_dir, input=task.encode("utf-8"), stdout=log, stderr=subprocess.STDOUT)


def task_text(items):
    lines = [f"{i + 1}) {k}.png — {line}" for i, (k, line) in enumerate(items)]
    return ("Use your imagegen skill (built-in image_gen tool, NOT the CLI fallback). "
            f"Generate exactly {len(items)} image(s), one image_gen call each, then copy each final PNG into the "
            "current working directory with these exact file names. Do not edit any other file.\n\n"
            + "\n\n".join(lines) + "\n\nFinally print the saved file paths and the exact prompts you used.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--only", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--effort", default="medium", help="Codex reasoning effort for the run")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    raw = json.loads((project / "gen_prompts.json").read_text(encoding="utf-8"))
    style_all = raw.get("_style") or DEFAULT_STYLE
    specs = {}
    for k, v in raw.items():
        if k.startswith("_") or (a.only and k not in a.only):
            continue
        v = {"prompt": v} if isinstance(v, str) else dict(v)
        if not v.get("prompt"):
            sys.exit(f"{k}: needs a prompt")
        v["refs"] = [project / r for r in v.get("refs", [])]
        specs[k] = v
    theme_path = project / "theme.json"
    th = json.loads(theme_path.read_text(encoding="utf-8")) if theme_path.exists() else {}
    palette = (f" Lighting and palette: rim light in {th['accent']} against a deep background close to {th['bg']}."
               if th.get("accent") and th.get("bg") else "")
    out_dir = project / "assets" / "images" / "gen"
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = {k: v for k, v in specs.items() if not (out_dir / f"{k}.png").exists()}
    if not todo:
        print("all images already exist; delete one to regenerate it")
        return

    def line(v):
        return (f"{v['prompt'].strip()} {v.get('style') or style_all} {GUARD}{palette}"
                + (f" {REF_NOTE}" if v["refs"] else ""))

    plain = [(k, line(v)) for k, v in todo.items() if not v["refs"]]
    with_refs = [(k, v) for k, v in todo.items() if v["refs"]]
    prompt_log = []
    if plain:
        t = task_text(plain)
        prompt_log.append(t)
        if not a.dry_run:
            run_codex(t, out_dir, [], a.effort, "codex_run.log")
    for k, v in with_refs:
        t = task_text([(k, line(v))])
        prompt_log.append(f"[refs: {', '.join(r.relative_to(project).as_posix() for r in v['refs'])}]\n{t}")
        if a.dry_run:
            continue
        missing_refs = [r for r in v["refs"] if not r.exists()]
        if missing_refs:
            print(f"skip    {k}: reference not found: {', '.join(map(str, missing_refs))}")
            continue
        run_codex(t, out_dir, v["refs"], a.effort, f"codex_run_{k}.log")
    (out_dir / "codex_prompt.txt").write_text("\n\n---\n\n".join(prompt_log), encoding="utf-8")
    if a.dry_run:
        print("\n\n---\n\n".join(prompt_log))
        return
    missing = [k for k in todo if not (out_dir / f"{k}.png").exists()]
    for k in todo:
        print(("missing " if k in missing else "saved   ") + str(out_dir / f"{k}.png"))
    if missing:
        sys.exit("some images were not produced — see the codex_run*.log files in assets/images/gen/")


if __name__ == "__main__":
    main()
