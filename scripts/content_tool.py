import argparse
import json
import re
from pathlib import Path

from build_compendiums import resolve_pack
from validate_content_source import ROOT, load_and_validate_content


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def fail(msg: str) -> None:
    raise SystemExit(msg)


def get_system_version() -> str:
    payload = json.loads((ROOT / "system.json").read_text(encoding="utf-8"))
    version = payload.get("version")
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        fail("system.json version is missing or invalid")
    return version


def slug_from_pathway_id(pathway_id: str) -> str:
    return pathway_id.split(".")[-1]


def base_item_system(entry_type: str, entry_id: str, name: str, system_version: str) -> dict:
    system = {
        "id": entry_id,
        "schemaVersion": 1,
        "name": name,
        "type": entry_type,
        "pathwayId": "pathway.seer",
        "allowedPathwayIds": ["pathway.seer"],
        "sequence": 9,
        "minSequence": 9,
        "sourceSequence": 9,
        "activation": "action",
        "resource": "spirit",
        "cost": 0,
        "cooldown": 0,
        "complexityClass": "invocation.standard_scope",
        "formulaKey": "check.skill.v1",
        "effects": [],
        "tags": ["draft"],
        "dependencies": {
            "minSystemVersion": system_version,
            "maxTestedSystemVersion": system_version,
            "requiresIds": [],
        },
        "pathwayData": {
            "displayName": "",
            "theme": "",
            "progressionNote": "",
        },
        "sequenceData": {
            "title": "",
            "summary": "",
            "milestones": [],
        },
    }

    if entry_type == "pathway":
        system["activation"] = "passive"
        system["resource"] = "none"
        system["pathwayData"] = {
            "displayName": name,
            "theme": "placeholder",
            "progressionNote": "Replace with progression notes.",
        }
        return system

    if entry_type == "sequenceNode":
        system["activation"] = "passive"
        system["resource"] = "none"
        system["sequenceData"] = {
            "title": name,
            "summary": "Replace with sequence summary.",
            "milestones": [],
        }
        return system

    if entry_type == "ability":
        system["abilityData"] = {
            "targetMode": "special",
            "rangeFt": 0,
            "attackAttribute": "wil",
            "linkedSkillId": "",
            "weaponAccuracy": 0,
        }
        return system

    if entry_type == "weapon":
        system["resource"] = "none"
        system["formulaKey"] = "check.attack.v1"
        system["weaponData"] = {
            "baseDamage": 1,
            "damageType": "physical",
            "rangeFt": 5,
            "accuracyBonus": 0,
        }
        return system

    if entry_type == "armor":
        system["activation"] = "passive"
        system["resource"] = "none"
        system["formulaKey"] = "check.attribute.v1"
        system["armorData"] = {
            "defenseShift": 0,
            "damageReduction": 0,
            "encumbrancePenalty": 0,
        }
        return system

    if entry_type == "ritual":
        system["activation"] = "special"
        system["resource"] = "spirit"
        system["formulaKey"] = "check.ritual.v1"
        system["ritualData"] = {
            "targetMode": "scene",
            "mandatoryComponents": 0,
            "baseCastMinutes": 10,
        }
        return system

    if entry_type == "artifact":
        system["activation"] = "special"
        system["resource"] = "none"
        system["artifactData"] = {
            "riskClass": "stable",
            "charges": 0,
            "misuseCorruptionGain": 0,
        }
        return system

    return system


def base_entry(entry_type: str, entry_id: str, name: str, system_version: str) -> dict:
    root = {
        "id": entry_id,
        "pack": "draft",
        "name": name,
        "version": system_version,
        "minSystemVersion": system_version,
        "maxTestedSystemVersion": system_version,
        "dependencies": [],
    }

    if entry_type == "rolltable":
        root.update(
            {
                "documentType": "RollTable",
                "pack": "rolltables",
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
                    "identity": {
                        "pathwayId": "pathway.none",
                        "sequence": 9,
                        "tier": "low",
                        "backgroundId": "background.civilian",
                    },
                    "attributes": {
                        k: {"base": 10, "temp": 0}
                        for k in ["str", "dex", "wil", "con", "cha", "int", "luck"]
                    },
                    "skills": {"investigation": {"linkedAttr": "int", "rank": "trained", "misc": 0}},
                    "derived": {
                        "hpMax": 50,
                        "spiritMax": 40,
                        "sanityMax": 55,
                        "defenseShift": 0,
                        "initiativeTarget": 35,
                    },
                    "resources": {"hp": 50, "spirit": 40, "corruption": 0, "deathMarks": 0, "deathSaves": 0},
                    "progression": {"gates": {"narrative": False, "economy": False, "stability": True}, "attemptState": "idle"},
                    "creation": {
                        "state": "complete",
                        "completedSteps": ["identity", "attributes", "skills", "pathway", "equipment"],
                        "version": 1,
                    },
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
            "pack": "draft-items",
            "system": base_item_system(entry_type, entry_id, name, system_version),
        }
    )
    return root


def pathway_bundle(pathway_id: str, pathway_name: str, top_sequence: int, bottom_sequence: int, system_version: str) -> dict:
    if top_sequence < bottom_sequence:
        fail("--top-sequence must be >= --bottom-sequence")
    if top_sequence > 9 or bottom_sequence < 0:
        fail("sequence bounds must stay within 0..9")

    slug = slug_from_pathway_id(pathway_id)
    entries = []

    pathway_entry = {
        "id": pathway_id,
        "pack": "pathways",
        "documentType": "Item",
        "itemType": "pathway",
        "name": f"Pathway: {pathway_name}",
        "version": system_version,
        "minSystemVersion": system_version,
        "maxTestedSystemVersion": system_version,
        "dependencies": [],
        "system": base_item_system("pathway", pathway_id, f"Pathway: {pathway_name}", system_version),
    }
    pathway_entry["system"]["pathwayId"] = pathway_id
    pathway_entry["system"]["pathwayData"]["displayName"] = pathway_name
    entries.append(pathway_entry)

    previous_sequence_id = None
    for sequence in range(top_sequence, bottom_sequence - 1, -1):
        sequence_id = f"sequence.{slug}.{sequence}"
        dependencies = [pathway_id]
        if previous_sequence_id:
            dependencies.append(previous_sequence_id)

        entry = {
            "id": sequence_id,
            "pack": "pathways",
            "documentType": "Item",
            "itemType": "sequenceNode",
            "name": f"{pathway_name} Sequence {sequence}",
            "version": system_version,
            "minSystemVersion": system_version,
            "maxTestedSystemVersion": system_version,
            "dependencies": dependencies,
            "system": base_item_system("sequenceNode", sequence_id, f"{pathway_name} Sequence {sequence}", system_version),
        }
        entry["system"]["pathwayId"] = pathway_id
        entry["system"]["sequence"] = sequence
        entry["system"]["minSequence"] = sequence
        entry["system"]["sequenceData"]["title"] = f"{pathway_name} Sequence {sequence}"
        entry["system"]["dependencies"]["requiresIds"] = dependencies
        entries.append(entry)

        previous_sequence_id = sequence_id

    return {"entries": entries}


def command_new(args):
    system_version = get_system_version()
    entry = base_entry(args.type, args.id, args.name, system_version)
    payload = {"entries": [entry]}

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"[content-tool] wrote template -> {output}")
    else:
        print(json.dumps(payload, indent=2))


def command_new_pathway_bundle(args):
    system_version = get_system_version()
    payload = pathway_bundle(args.pathway_id, args.pathway_name, args.top_sequence, args.bottom_sequence, system_version)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"[content-tool] wrote pathway bundle scaffold -> {output}")
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


def command_bump_max_tested(args):
    version = args.version.strip()
    if not SEMVER_RE.fullmatch(version):
        fail("--version must be semver X.Y.Z")

    files = sorted((ROOT / "content-src").rglob("*.json"))
    if not files:
        fail("No content source files found under content-src")

    changed_files = 0
    changed_entries = 0
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload.get("entries", [])
        if not isinstance(entries, list):
            continue

        file_changed = False
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            if entry.get("maxTestedSystemVersion") != version:
                entry["maxTestedSystemVersion"] = version
                file_changed = True
                changed_entries += 1

            if entry.get("documentType") == "Item":
                system = entry.get("system")
                if isinstance(system, dict):
                    deps = system.get("dependencies")
                    if isinstance(deps, dict) and deps.get("maxTestedSystemVersion") != version:
                        deps["maxTestedSystemVersion"] = version
                        file_changed = True

        if file_changed:
            changed_files += 1
            if args.write:
                path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    mode = "write" if args.write else "preview"
    print(
        "[content-tool] bump-max-tested "
        f"({mode}) version={version} changed_entries={changed_entries} changed_files={changed_files}"
    )
    if not args.write and changed_files > 0:
        print("[content-tool] rerun with --write to apply changes")


def main():
    parser = argparse.ArgumentParser(description="LoTM content authoring helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Generate a starter content entry template")
    p_new.add_argument("--type", required=True, help="Item type or one of: rolltable, actor, journal")
    p_new.add_argument("--id", required=True, help="Content ID")
    p_new.add_argument("--name", required=True, help="Display name")
    p_new.add_argument("--output", help="Optional output json file path")
    p_new.set_defaults(func=command_new)

    p_bundle = sub.add_parser("new-pathway-bundle", help="Generate pathway + sequence scaffold bundle")
    p_bundle.add_argument("--pathway-id", required=True, help="Pathway ID (example: pathway.seer)")
    p_bundle.add_argument("--pathway-name", required=True, help="Pathway display name")
    p_bundle.add_argument("--top-sequence", type=int, default=9, help="Top sequence in scaffold range (default: 9)")
    p_bundle.add_argument("--bottom-sequence", type=int, default=7, help="Bottom sequence in scaffold range (default: 7)")
    p_bundle.add_argument("--output", help="Optional output json file path")
    p_bundle.set_defaults(func=command_new_pathway_bundle)

    p_lint = sub.add_parser("lint", help="Run content validation")
    p_lint.set_defaults(func=command_lint)

    p_preview = sub.add_parser("preview", help="Show resolved pack destination for each entry")
    p_preview.set_defaults(func=command_preview)

    p_bump = sub.add_parser(
        "bump-max-tested",
        help="Bulk bump maxTestedSystemVersion metadata without changing gameplay semantics",
    )
    p_bump.add_argument("--version", required=True, help="Semver target for maxTestedSystemVersion")
    p_bump.add_argument("--write", action="store_true", help="Apply edits (default is preview only)")
    p_bump.set_defaults(func=command_bump_max_tested)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
