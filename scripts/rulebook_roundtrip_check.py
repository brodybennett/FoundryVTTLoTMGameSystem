import argparse
import html
import re
import sys
import zipfile
from pathlib import Path


REQUIRED_SNIPPETS = [
    "FinalTarget = clamp(BaseTarget + Modifiers - Penalties, 1, 95)",
    "There is no universal Bonus Action",
    "SkillTarget = clamp(",
    "CorruptionPenalty = max(-6, -1 * floor(CurrentCorruptionPct / 10))",
    "\"type\": \"ability\"",
]

BANNED_PATTERNS = [
    r"\b1\s+Bonus\s+Action\b",
    r"clamp\([^)]*,\s*1\s*,\s*100\)",
    r"30\s*\+\s*floor\(\s*Linked\s*Attribute\s*/\s*2\)",
    r"Corruption[^\\n]{0,120}-(?:7|8|9|10)",
]


def fail(msg: str) -> None:
    print(f"[roundtrip] FAIL: {msg}")
    sys.exit(1)


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        data = zf.read("word/document.xml").decode("utf-8")
    text = data.replace("</w:p>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Roundtrip check for generated rulebook docx.")
    parser.add_argument("--docx", required=True, help="Path to generated .docx file")
    args = parser.parse_args()

    docx_path = Path(args.docx)
    if not docx_path.exists():
        fail(f"docx not found: {docx_path}")

    text = extract_docx_text(docx_path)

    missing = [s for s in REQUIRED_SNIPPETS if s not in text]
    if missing:
        fail(f"missing required snippet(s): {missing}")

    found = []
    for pattern in BANNED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(pattern)
    if found:
        fail(f"found banned pattern(s): {found}")

    print("[roundtrip] PASS")


if __name__ == "__main__":
    main()

