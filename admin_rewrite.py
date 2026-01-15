import os
import json
import argparse
import subprocess
from pathlib import Path
from datetime import date, datetime

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# ---------------------------
# Helpers
# ---------------------------

def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def parse_yyyy_mm_dd(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def clamp_x(text: str, max_chars: int) -> str:
    """Best-effort clamp to max chars; prefer templates that already fit."""
    t = " ".join(text.split())
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1].rstrip() + "…"

def format_int(n: int) -> str:
    return f"{n:,}"

def compute_vars(cfg: dict) -> dict:
    today = date.today()
    start = parse_yyyy_mm_dd(cfg["start_date"])
    days = (today - start).days
    if days < 0:
        days = 0

    killed = int(cfg.get("killed_estimate", 0))

    return {
        "country": cfg.get("country", "Iran"),
        "start_date": start.strftime("%Y-%m-%d"),
        "today": today.strftime("%Y-%m-%d"),
        "days": days,
        "days_phrase": f"{days} days" if days != 1 else "1 day",
        "killed_estimate": killed,
        "killed_estimate_fmt": format_int(killed),
        "injured_phrase": cfg.get("injured_phrase", "countless injured"),
        "regime_terms": cfg.get("regime_terms", "the Islamic regime and the IRGC"),
    }

def fill(template: str, vars_: dict) -> str:
    return template.format(**vars_)

def get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    if not OpenAI:
        return None
    return OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
Rewrite sensitive informational messages.

Rules:
- Keep meaning identical.
- Neutral, factual tone.
- One sentence only for X messages.
- Max characters as requested.
- No emojis.
- No quotes.
Return exactly N lines, each a standalone variant.
""".strip()

def clean_lines(text: str, n: int) -> list[str]:
    lines = []
    for raw in text.split("\n"):
        s = raw.strip()
        if not s:
            continue
        s = s.strip(" -•\t")
        s = s.lstrip("0123456789. )(").strip()
        if s:
            lines.append(s)
        if len(lines) >= n:
            break
    return lines[:n]

def ai_paraphrase_variants(client, base_text: str, n: int, max_chars: int, kind: str) -> list[str]:
    if kind == "x":
        user_prompt = f"""
Create {n} paraphrases of the message in English.

Constraints:
- One sentence.
- Neutral, factual tone.
- Max {max_chars} characters.
- No hashtags.
- No emojis.

Message:
{base_text}
""".strip()
    else:
        user_prompt = f"""
Create {n} paraphrases of the message in English.

Constraints:
- Keep meaning.
- Neutral, factual tone.
- No emojis.
- Keep it concise.
Return each variant on a new line.

Message:
{base_text}
""".strip()

    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    out = clean_lines(resp.output_text, n)
    if kind == "x":
        out = [clamp_x(x, max_chars) for x in out]
    return out

def git_commit_and_push(files: list[str], message: str) -> bool:
    """
    Adds files, commits (if changes exist), then pushes.
    If push is rejected, user must pull/rebase manually (by design).
    """
    try:
        subprocess.run(["git", "add", *files], check=True)

        commit = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)
        if commit.returncode != 0:
            combined = (commit.stdout + "\n" + commit.stderr).lower()
            if "nothing to commit" in combined:
                print("i Git: nothing to commit.")
            else:
                print(commit.stdout)
                print(commit.stderr)
                return False

        push = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push.returncode != 0:
            print(push.stdout)
            print(push.stderr)
            return False

        print("✓ Git push completed")
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Git operation failed:", e)
        return False

# ---------------------------
# Template Library (works without AI)
# ---------------------------

X_SHORT_TEMPLATES = [
    "{country} is under an internet blackout again. Cutting connectivity enables concealment and impunity, and the world should not ignore it.",
    "Another internet blackout in {country}: when information is cut, abuses can escalate unseen and accountability disappears.",
    "{country} has gone dark online again. Blackouts are used to block documentation and suppress civilian voices."
]

X_FACTUAL_TEMPLATES = [
    "After {days_phrase} of a digital blaimport os
import json
import argparse
import subprocess
from pathlib import Path
from datetime import date, datetime

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# ---------------------------
# Helpers
# ---------------------------

def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def parse_yyyy_mm_dd(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def clamp_x(text: str, max_chars: int) -> str:
    """Best-effort clamp to max chars; prefer templates that already fit."""
    t = " ".join(text.split())
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1].rstrip() + "…"

def format_int(n: int) -> str:
    return f"{n:,}"

def compute_vars(cfg: dict) -> dict:
    today = date.today()
    start = parse_yyyy_mm_dd(cfg["start_date"])
    days = (today - start).days
    if days < 0:
        days = 0

    killed = int(cfg.get("killed_estimate", 0))

    return {
        "country": cfg.get("country", "Iran"),
        "start_date": start.strftime("%Y-%m-%d"),
        "today": today.strftime("%Y-%m-%d"),
        "days": days,
        "days_phrase": f"{days} days" if days != 1 else "1 day",
        "killed_estimate": killed,
        "killed_estimate_fmt": format_int(killed),
        "injured_phrase": cfg.get("injured_phrase", "countless injured"),
        "regime_terms": cfg.get("regime_terms", "the Islamic regime and the IRGC"),
    }

def fill(template: str, vars_: dict) -> str:
    return template.format(**vars_)

def get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    if not OpenAI:
        return None
    return OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
Rewrite sensitive informational messages.

Rules:
- Keep meaning identical.
- Neutral, factual tone.
- One sentence only for X messages.
- Max characters as requested.
- No emojis.
- No quotes.
Return exactly N lines, each a standalone variant.
""".strip()

def clean_lines(text: str, n: int) -> list[str]:
    lines = []
    for raw in text.split("\n"):
        s = raw.strip()
        if not s:
            continue
        s = s.strip(" -•\t")
        s = s.lstrip("0123456789. )(").strip()
        if s:
            lines.append(s)
        if len(lines) >= n:
            break
    return lines[:n]

def ai_paraphrase_variants(client, base_text: str, n: int, max_chars: int, kind: str) -> list[str]:
    if kind == "x":
        user_prompt = f"""
Create {n} paraphrases of the message in English.

Constraints:
- One sentence.
- Neutral, factual tone.
- Max {max_chars} characters.
- No hashtags.
- No emojis.

Message:
{base_text}
""".strip()
    else:
        user_prompt = f"""
Create {n} paraphrases of the message in English.

Constraints:
- Keep meaning.
- Neutral, factual tone.
- No emojis.
- Keep it concise.
Return each variant on a new line.

Message:
{base_text}
""".strip()

    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    out = clean_lines(resp.output_text, n)
    if kind == "x":
        out = [clamp_x(x, max_chars) for x in out]
    return out

def git_commit_and_push(files: list[str], message: str) -> bool:
    """
    Adds files, commits (if changes exist), then pushes.
    If push is rejected, user must pull/rebase manually (by design).
    """
    try:
        subprocess.run(["git", "add", *files], check=True)

        commit = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)
        if commit.returncode != 0:
            combined = (commit.stdout + "\n" + commit.stderr).lower()
            if "nothing to commit" in combined:
                print("i Git: nothing to commit.")
            else:
                print(commit.stdout)
                print(commit.stderr)
                return False

        push = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push.returncode != 0:
            print(push.stdout)
            print(push.stderr)
            return False

        print("✓ Git push completed")
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Git operation failed:", e)
        return False

# ---------------------------
# Template Library (works without AI)
# ---------------------------

X_SHORT_TEMPLATES = [
    "{country} is under an internet blackout again. Cutting connectivity enables concealment and impunity, and the world should not ignore it.",
    "Another internet blackout in {country}: when information is cut, abuses can escalate unseen and accountability disappears.",
    "{country} has gone dark online again. Blackouts are used to block documentation and suppress civilian voices."
]

X_FACTUAL_TEMPLATES = [
    "After {days_phrase} of a digital blackout in {country}, reports indicate over {killed_estimate_fmt} killed and {injured_phrase}; {regime_terms} are using the shutdown to conceal violence.",
    "{country} has faced {days_phrase} of internet blackout since {start_date}; reports cite over {killed_estimate_fmt} killed and {injured_phrase} as {regime_terms} restrict visibility.",
    "Internet access in {country} has been restricted for {days_phrase}; reports suggest over {killed_estimate_fmt} killed and {injured_phrase} while {regime_terms} limit documentation."
]

X_CTA_TEMPLATES = [
    "{country}’s internet blackout is a cover-up by {regime_terms}. Reports cite over {killed_estimate_fmt} killed after {days_phrase}. Global leaders must act now.",
    "Silence enables violence: {regime_terms} use blackouts in {country} to conceal abuses. After {days_phrase}, reports cite over {killed_estimate_fmt} killed—urgent action is needed.",
    "A digital blackout in {country} is erasing accountability. After {days_phrase}, reports cite over {killed_estimate_fmt} killed. This demands immediate international pressure."
]

IG_CAPTION_TEMPLATES = [
    "{country} is facing an internet blackout while violence escalates.\n\nWhen access is cut, documentation stops and accountability disappears.\n\n{hashtags}",
    "Another internet shutdown in {country} is keeping the world from seeing what is happening.\n\nSilence is being enforced to conceal violence.\n\n{hashtags}",
    "When {country} goes dark online, the truth goes dark too.\n\nBlackouts protect abuses, not people.\n\n{hashtags}"
]

IG_STORY_TEMPLATES = [
    "Internet blackout in {country}\n\n{days_phrase} offline\n\nSpeak up. Share.",
    "{country} is offline\n\nBlackouts hide violence\n\nDo not look away.",
    "No internet.\nNo transparency.\nNo accountability."
]

BIO_TEMPLATES = [
    "Internet blackouts hide violence. Demand transparency.",
    "Stop digital blackouts. Demand accountability.",
    "Blackouts conceal abuses. Speak up for {country}."
]

def build_output(cfg: dict, vars_: dict, use_ai: bool, n_x: int, n_ig: int) -> dict:
    max_x = int(cfg.get("limits", {}).get("x_max_chars", 190))
    hashtags_x = cfg.get("hashtags", {}).get("x", "")
    hashtags_ig = cfg.get("hashtags", {}).get("instagram", "")

    client = get_client() if use_ai else None

    def gen_from_templates(templates: list[str], count: int) -> list[str]:
        out = []
        for t in templates:
            out.append(fill(t, vars_))
            if len(out) >= count:
                break
        return out[:count]

    # ---- X ----
    x_short = [clamp_x(m, max_x) for m in gen_from_templates(X_SHORT_TEMPLATES, n_x)]
    x_factual = [clamp_x(m, max_x) for m in gen_from_templates(X_FACTUAL_TEMPLATES, n_x)]
    x_cta = [clamp_x(m, max_x) for m in gen_from_templates(X_CTA_TEMPLATES, n_x)]

    # Optional AI paraphrase (generates n variants from first template)
    if client:
        if x_short:
            x_short = ai_paraphrase_variants(client, x_short[0], n_x, max_x, "x")
        if x_factual:
            x_factual = ai_paraphrase_variants(client, x_factual[0], n_x, max_x, "x")
        if x_cta:
            x_cta = ai_paraphrase_variants(client, x_cta[0], n_x, max_x, "x")

    # ---- Instagram ----
    ig_caption = [fill(t, {**vars_, "hashtags": hashtags_ig}) for t in IG_CAPTION_TEMPLATES][:n_ig]
    ig_story = [fill(t, vars_) for t in IG_STORY_TEMPLATES][:n_ig]

    # Optional AI paraphrase for IG (keeps multi-line allowed)
    if client:
        if ig_caption:
            ig_caption = ai_paraphrase_variants(client, ig_caption[0], n_ig, max_x, "instagram_caption")
            ig_caption = [c if hashtags_ig in c else (c.rstrip() + "\n\n" + hashtags_ig) for c in ig_caption]
        if ig_story:
            ig_story = ai_paraphrase_variants(client, ig_story[0], n_ig, max_x, "instagram_story")

    # ---- Bio ----
    bio = [fill(t, vars_) for t in BIO_TEMPLATES][:max(3, min(6, n_ig))]

    return {
        "generated": {
            "today": vars_["today"],
            "start_date": vars_["start_date"],
            "days_since_start": vars_["days"],
            "killed_estimate": vars_["killed_estimate"],
        },
        "hashtags": {
            "x": hashtags_x,
            "instagram": hashtags_ig
        },
        "messages": {
            "x": {
                "short": x_short,
                "factual": x_factual,
                "cta": x_cta
            },
            "instagram": {
                "caption": ig_caption,
                "story": ig_story
            },
            "bio": bio
        }
    }

def main():
    parser = argparse.ArgumentParser(
        description="Generate microlink data.json with X/Instagram/Bio sections + variables (no backups)."
    )
    parser.add_argument("--config", default="config.json", help="Config file path (default: config.json)")
    parser.add_argument("--file", default="data.json", help="Output JSON file path (default: data.json)")
    parser.add_argument("--write", action="store_true", help="Overwrite output JSON file.")
    parser.add_argument("--x-n", type=int, default=3, help="Number of variants per X group (default: 3)")
    parser.add_argument("--ig-n", type=int, default=3, help="Number of variants per IG group (default: 3)")
    parser.add_argument("--ai", action="store_true", help="Use OpenAI to paraphrase templates (requires OPENAI_API_KEY).")
    parser.add_argument("--push", action="store_true", help="git add/commit/push after writing.")
    args = parser.parse_args()

    cfg = load_json(Path(args.config))
    vars_ = compute_vars(cfg)
    out = build_output(cfg, vars_, use_ai=args.ai, n_x=args.x_n, n_ig=args.ig_n)

    print("\n=== GENERATED JSON (preview) ===\n")
    print(json.dumps(out, ensure_ascii=False, indent=2))

    if args.write:
        target = Path(args.file)
        target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("\n=== WROTE FILE ===")
        print(f"Updated: {target.resolve()}")

        if args.push:
            ok = git_commit_and_push([args.file], f"Update messages ({vars_['today']})")
            if ok:
                print("=== PUSH OK ===")
            else:
                print("=== PUSH FAILED (see output above) ===")

if __name__ == "__main__":
    main()
ckout in {country}, reports indicate over {killed_estimate_fmt} killed and {injured_phrase}; {regime_terms} are using the shutdown to conceal violence.",
    "{country} has faced {days_phrase} of internet blackout since {start_date}; reports cite over {killed_estimate_fmt} killed and {injured_phrase} as {regime_terms} restrict visibility.",
    "Internet access in {country} has been restricted for {days_phrase}; reports suggest over {killed_estimate_fmt} killed and {injured_phrase} while {regime_terms} limit documentation."
]

X_CTA_TEMPLATES = [
    "{country}’s internet blackout is a cover-up by {regime_terms}. Reports cite over {killed_estimate_fmt} killed after {days_phrase}. Global leaders must act now.",
    "Silence enables violence: {regime_terms} use blackouts in {country} to conceal abuses. After {days_phrase}, reports cite over {killed
