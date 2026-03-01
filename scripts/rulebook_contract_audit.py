import argparse
import re
import sys
from pathlib import Path


REQUIRED_PATTERNS = [
    r"FinalTarget\s*=\s*clamp\([^)]*1\s*,\s*95\)",
    r"AttackTarget\s*=\s*clamp\(",
    r"FinalDamage\s*=\s*max\(1\s*,\s*floor\(",
    r"no universal Bonus Action",
    r"SkillTarget\s*=\s*clamp\(\s*25\s*\+\s*floor\(LinkedAttribute\s*/\s*3\)\s*\+\s*ProficiencyBonus\s*\+\s*floor\(LUCK\s*/\s*10\)",
    r"CorruptionPenalty\s*=\s*lookupBandPenalty\(CurrentCorruptionPct\)",
    r"70-79\s*=>\s*-7",
    r"90-100\s*=>\s*-10",
    r"Corruption is tracked in integer points from\s*`?0`?\s*to\s*`?100`?",
    r"DeathTarget\s*=\s*clamp\(50\s*\+\s*floor\(CON\s*/\s*2\)\s*-\s*min\(6\s*,\s*floor\(CorruptionPct\s*/\s*10\)\)\s*,\s*1\s*,\s*95\)",
    r"channeling:\s*`willpower`\s*by default,\s*or\s*`endurance`\s*if declared before rolling",
    r"RitualTarget\s*=\s*clamp\([\s\S]*?\+\s*CorruptionPenalty",
    r"RitualTarget\s*=\s*clamp\([\s\S]*?floor\(\(WIL\s*\+\s*INT\s*\+\s*LUCK\)\s*/\s*9\)",
    r"ability\.minSequence\s*<=\s*ability\.sequence",
    r"sourceCategory[\s`]*is required",
    r"target[\s`]*is required",
    r"trigger[\s`]*is required",
    r"\"type\"\s*:\s*\"ability\"",
    r"\"schemaVersion\"\s*:\s*1",
]


BANNED_PATTERNS = [
    r"\b1\s+Bonus\s+Action\b",
    r"clamp\([^)]*,\s*1\s*,\s*100\)",
    r"30\s*\+\s*floor\(\s*Linked\s*Attribute\s*/\s*2\)",
    r"CorruptionPenalty\s*=\s*max\(",
    r"Corruption[^\\n]{0,180}-(?:1[1-9]|[2-9][0-9])",
    r"RitualTarget[^\\n]{0,180}-\s*CorruptionPenalty",
    r"floor\(\(WIL\s*\+\s*INT\s*\+\s*LUCK\)\s*/\s*3\)",
    r"corruptionGainPctOfMaxSanity",
    r"willpower_or_endurance",
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
