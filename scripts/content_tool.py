import argparse
import json
from pathlib import Path

from validate_content_source import ROOT, load_and_validate_content
from build_compendiums import resolve_pack


SYSTEM_VERSION = "1.2.2"


def fail(msg: str) -> None:
    raise SystemExit(msg)


def base_entry(entry_type: str, entry_id: str, name: str) -> dict:
    root = {
        "id": entry_id,
        "pack": "draft",
        "name": name,
        "version": SYSTEM_VERSION,
        "minSystemVersion": SYSTEM_VERSION,
        "maxTestedSystemVersion": SYSTEM_VERSION,
        "dependencies": [],
    }

    if entry_type == "rolltable":
        root.update(
            {
                "documentType": "RollTable",
                "segment": "abilities",
                "formula": "1d1",
                "results": [{"text": "Placeholder result", "weight": 1}],
                "triggerTags": ["placeholder"],
            }
        )
        return root

    if entry_type == "actor":
        root.update(
            {
                "documentType": "Actor",
                "actorType": "npc",
                "pack": "actors-civilians",
                "system": {
                    "identity": {"pathwayId": "pathway.none", "sequence": 9, "tier": "low", "backgroundId": "background.civilian"},
                    "attributes": {k: {"base": 10, "temp": 0} for k in ["str", "dex", "wil", "con", "cha", "int", "luck"]},
                    "skills": {
                        "investigation": {"linkedAttr": "int", "rank": "trained", "misc": 0}
                    },
                    "derived": {"hpMax": 50, "spiritMax": 40, "sanityMax": 55, "defenseShift": 0, "initiativeTarget": 35},
                    "resources": {"hp": 50, "spirit": 40, "corruption": 0, "deathMarks": 0, "deathSaves": 0},
                    "progression": {"gates": {"narrative": False, "economy": False, "stability": True}, "attemptState": "idle"},
                    "creation": {"state": "complete", "completedSteps": ["identity", "attributes", "skills", "pathway", "equipment"], "version": 1},
                    "version": {"schemaVersion": 1},
                },
            }
        )
        return root

    if entry_type == "journal":
        root.update(
            {
                "documentType": "JournalEntry",
                "pack": "rules-reference",
                "pages": [{"title": "Section", "format": 1, "content": "<p>Replace with rule text.</p>"}],
            }
        )
        return root

    root.update(
        {
            "documentType": "Item",
            "itemType": entry_type,
            "system": {
                "id": entry_id,
                "schemaVersion": 1,
                "name": name,
                "type": entry_type,
                "pathwayId": "pathway.seer",
                "sequence": 9,
                "minSequence": 9,
                "activation": "action",
                "resource": "spirit",
                "cost": 0,
                "cooldown": 0,
                "formulaKey": "check.skill.v1",
                "effects": [],
                "tags": ["draft"],
                "dependencies": {
                    "minSystemVersion": SYSTEM_VERSION,
                    "maxTestedSystemVersion": SYSTEM_VERSION,
                    "requiresIds": [],
                },
                "abilityData": {"targetMode": "special"},
                "ritualData": {"targetMode": "scene", "mandatoryComponents": 0, "baseCastMinutes": 10},
                "artifactData": {"riskClass": "stable", "charges": 0, "misuseCorruptionGain": 0},
                "weaponData": {"baseDamage": 1, "damageType": "physical", "rangeFt": 5, "accuracyBonus": 0},
                "armorData": {"defenseShift": 0, "damageReduction": 0, "encumbrancePenalty": 0},
            },
        }
    )
    return root


def command_new(args):
    entry = base_entry(args.type, args.id, args.name)
    payload = {"entries": [entry]}

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"[content-tool] wrote template -> {output}")
    else:
        print(json.dumps(payload, indent=2))


def command_lint(_args):
    entries, warnings = load_and_validate_content()
    print(f"[content-tool] content lint pass ({len(entries)} entries)")
    if warnings:
        print("[content-tool] warnings:")
        for warning in warnings:
            print(f"  - {warning}")


def command_preview(_args):
    entries, _ = load_and_validate_content()
    print("[content-tool] pack preview")
    for entry in sorted(entries, key=lambda item: item["id"]):
        print(f"  - {entry['id']} -> {resolve_pack(entry)}")


def main():
    parser = argparse.ArgumentParser(description="LoTM content authoring helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Generate a starter content entry template")
    p_new.add_argument("--type", required=True, help="Item type or one of: rolltable, actor, journal")
    p_new.add_argument("--id", required=True, help="Content ID")
    p_new.add_argument("--name", required=True, help="Display name")
    p_new.add_argument("--output", help="Optional output json file path")
    p_new.set_defaults(func=command_new)

    p_lint = sub.add_parser("lint", help="Run content validation")
    p_lint.set_defaults(func=command_lint)

    p_preview = sub.add_parser("preview", help="Show resolved pack destination for each entry")
    p_preview.set_defaults(func=command_preview)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
