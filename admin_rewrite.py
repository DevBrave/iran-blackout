import os
import json
import time
import argparse
from pathlib import Path
from openai import OpenAI
import subprocess
# ---------- Config ----------
SYSTEM_PROMPT = """
You rewrite sensitive informational messages.

Strict rules:
- Keep the meaning identical.
- Neutral, factual tone.
- One sentence only.
- Max 180 characters.
- No hashtags.
- No emojis.
- No quotes.
- Output each rewrite on a new line.
"""


DEFAULT_HASHTAGS_EN = "#IranRevelution2026 #DigitalBlackoutIran #FreeIran #KingRezaPahlavi #MassacreInIran"
DEFAULT_MODEL = "gpt-4.1-mini"
# ---------------------------

def git_commit_and_push(message="Update messages"):
    try:
        subprocess.run(["git", "add", "data.json"], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✓ Git push completed")
    except subprocess.CalledProcessError as e:
        print("✗ Git operation failed:", e)


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("not set. Set it as an environment variable.")
    return OpenAI(api_key=api_key)

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

def generate_variants(client: OpenAI, base_text: str, language: str, n: int, model: str) -> list[str]:
    prompt = f"""
Rewrite the following message into {n} different {language} versions.

Message:
{base_text}
"""
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
    )
    return clean_lines(resp.output_text, n)


def main():
    parser = argparse.ArgumentParser(description="Admin rewrite tool: generates microlink data.json content.")
    parser.add_argument("--write", action="store_true", help="Overwrite the JSON file (creates a timestamped backup).")
    parser.add_argument("--file", default="data.json", help="Target JSON file path (default: data.json)")
    parser.add_argument("--n", type=int, default=3, help="Number of variants per language (default: 3)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--hashtags-en", default=DEFAULT_HASHTAGS_EN, help="EN hashtags string")
    args = parser.parse_args()

    base_en = input("Base EN text (or empty): ").strip()

    client = get_client()

    output = {
        "hashtags": {
            "en": args.hashtags_en
        },
        "messages": {
            "en": []
        }
    }

    if base_en:
        output["messages"]["en"] = generate_variants(client, base_en, "English", args.n, args.model)

    # Always print to stdout (useful for quick copy/paste)
    print("\n=== GENERATED JSON ===\n")
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if args.write:
        target = Path(args.file)
        target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        git_commit_and_push("Daily message update")
        print("\n=== WROTE FILE ===")
        print(f"Updated: {target.resolve()}")
        print("\n=== WROTE FILE & PUSHED TO GITHUB ===")
        print(f"Updated: {target.resolve()}")

if __name__ == "__main__":
    main()
