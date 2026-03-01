import argparse
import re
import sys
from pathlib import Path


REQUIRED_PATTERNS = [
    r"FinalTarget\s*=\s*clamp\([^)]*1\s*,\s*95\)",
    r"no universal Bonus Action",
    r"SkillTarget\s*=\s*clamp\(\s*25\s*\+\s*floor\(LinkedAttribute\s*/\s*3\)\s*\+\s*ProficiencyBonus\s*\+\s*floor\(LUCK\s*/\s*10\)",
    r"CorruptionPenalty\s*=\s*max\(\s*-6\s*,\s*-1\s*\*\s*floor\(CurrentCorruptionPct\s*/\s*10\)\s*\)",
    r"RitualTarget\s*=\s*clamp\([\s\S]*?\+\s*CorruptionPenalty",
    r"ability\.minSequence\s*<=\s*ability\.sequence",
    r"sourceCategory[\s`]*is required",
    r"\"type\"\s*:\s*\"ability\"",
    r"\"schemaVersion\"\s*:\s*1",
]


BANNED_PATTERNS = [
    r"\b1\s+Bonus\s+Action\b",
    r"clamp\([^)]*,\s*1\s*,\s*100\)",
    r"30\s*\+\s*floor\(\s*Linked\s*Attribute\s*/\s*2\)",
    r"Corruption[^\\n]{0,120}-(?:7|8|9|10)",
    r"RitualTarget[^\\n]{0,180}-\s*CorruptionPenalty",
]


def fail(msg: str) -> None:
    print(f"[contract-audit] FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit canonical rulebook contract markers.")
    parser.add_argument("--rulebook", required=True, help="Path to markdown rulebook source file.")
    args = parser.parse_args()

    path = Path(args.rulebook)
    if not path.exists():
        fail(f"Rulebook file not found: {path}")

    text = path.read_text(encoding="utf-8")

    missing = []
    for pattern in REQUIRED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is None:
            missing.append(pattern)
    if missing:
        fail(f"Missing required canonical pattern(s): {missing}")

    found_banned = []
    for pattern in BANNED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None:
            found_banned.append(pattern)
    if found_banned:
        fail(f"Found banned pattern(s): {found_banned}")

    print("[contract-audit] PASS")


if __name__ == "__main__":
    main()
