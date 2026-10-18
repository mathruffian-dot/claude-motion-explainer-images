"""Generate illustration images through the local Codex CLI's imagegen skill (built-in image_gen).

gen_prompts.json (project root):
{
  "hook-loop":  "Cinematic wide 16:9 photo-illustration. A sleek unbranded electric hypercar driving upside down ...",
  "hover-jets": "..."
}
Every prompt gets the film's guard rails appended: no logos/badges/text/real brands, the theme's
background and accent colours from theme.json, and room for text overlay. Images land in
<project>/assets/images/gen/<name>.png. Label them 「AI 生成示意圖」 on screen.

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
         "not any real brand's design. Photoreal, high contrast, sharp.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--only", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--effort", default="medium", help="Codex reasoning effort for the run")
    a = ap.parse_args()
    project = Path(a.project).resolve()
    prompts = json.loads((project / "gen_prompts.json").read_text(encoding="utf-8"))
    prompts = {k: v for k, v in prompts.items() if not k.startswith("_") and (not a.only or k in a.only)}
    theme_path = project / "theme.json"
    th = json.loads(theme_path.read_text(encoding="utf-8")) if theme_path.exists() else {}
    palette = (f" Lighting and palette: rim light in {th['accent']} against a deep background close to {th['bg']}."
               if th.get("accent") and th.get("bg") else "")
    out_dir = project / "assets" / "images" / "gen"
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = {k: v for k, v in prompts.items() if not (out_dir / f"{k}.png").exists()}
    if not todo:
        print("all images already exist; delete one to regenerate it")
        return
    lines = [f"{i + 1}) {k}.png — {v.strip()} {GUARD}{palette}" for i, (k, v) in enumerate(todo.items())]
    task = ("Use your imagegen skill (built-in image_gen tool, NOT the CLI fallback). "
            f"Generate exactly {len(todo)} image(s), one image_gen call each, then copy each final PNG into the "
            "current working directory with these exact file names. Do not edit any other file.\n\n"
            + "\n\n".join(lines) + "\n\nFinally print the saved file paths and the exact prompts you used.")
    (out_dir / "codex_prompt.txt").write_text(task, encoding="utf-8")
    if a.dry_run:
        print(task)
        return
    codex = shutil.which("codex")  # on Windows this resolves codex.cmd, which a bare "codex" would not
    if not codex:
        sys.exit("codex CLI not found — install it, or generate the images another way into assets/images/gen/")
    with open(out_dir / "codex_run.log", "w", encoding="utf-8") as log:
        # the task goes in on stdin ("-"): a multi-line argument is mangled by codex.cmd on Windows,
        # and an open stdin with no input would make codex wait forever
        subprocess.run([codex, "exec", "--skip-git-repo-check", "-s", "workspace-write",
                        "-c", f"model_reasoning_effort={a.effort}", "-"],
                       cwd=out_dir, input=task.encode("utf-8"), stdout=log, stderr=subprocess.STDOUT)
    missing = [k for k in todo if not (out_dir / f"{k}.png").exists()]
    for k in todo:
        print(("missing " if k in missing else "saved   ") + str(out_dir / f"{k}.png"))
    if missing:
        sys.exit("some images were not produced — see assets/images/gen/codex_run.log")


if __name__ == "__main__":
    main()
