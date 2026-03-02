import hashlib
import json
from pathlib import Path

from validate_content_source import ROOT, load_and_validate_content

PACKS_DIR = ROOT / "packs"


def stable_id(content_id: str) -> str:
    return hashlib.md5(content_id.encode("utf-8")).hexdigest()[:16]


def title_from_pathway(pathway_id: str | None) -> str:
    if not pathway_id:
        return "Universal"
    return pathway_id.split(".")[-1].replace("_", " ").title()


def infer_rolltable_segment(entry: dict) -> str:
    explicit = entry.get("segment")
    if explicit:
        return explicit

    content_id = entry["id"]
    if "loot" in content_id:
        return "resources"
    if "corruption" in content_id:
        return "corruption"
    if "artifact" in content_id:
        return "artifacts"
    if "ritual" in content_id:
        return "rituals"
    if "encounter" in content_id:
        return "encounters"
    return "abilities"


def resolve_pack(entry: dict) -> str:
    doc_type = entry["documentType"]

    if doc_type == "Item":
        item_type = entry["itemType"]
        system = entry["system"]
        pathway_id = system.get("pathwayId")

        if item_type in {"pathway", "sequenceNode"}:
            slug = pathway_id.split(".")[-1] if pathway_id else "universal"
            return f"pathways-{slug}"
        if item_type == "ability":
            return "abilities"
        if item_type == "ritual":
            return "rituals"
        if item_type == "artifact":
            return "sealed-artifacts"
        if item_type == "weapon":
            return "items-weapons"
        if item_type == "armor":
            return "items-armor"
        if item_type == "consumable":
            return "items-consumables"
        if item_type == "ingredient":
            return "items-ingredients"
        return "items-gear"

    if doc_type == "RollTable":
        return f"rolltables-{infer_rolltable_segment(entry)}"

    return entry["pack"]


def with_grouped_name(entry: dict) -> str:
    name = entry["name"]
    if entry["documentType"] != "Item":
        return name

    item_type = entry["itemType"]
    system = entry["system"]

    if item_type in {"ability", "ritual"}:
        pathway_label = title_from_pathway(system.get("pathwayId"))
        seq = system.get("sequence")
        if isinstance(seq, int):
            return f"[{pathway_label} S{seq}] {name}"
        return f"[{pathway_label}] {name}"

    if item_type == "artifact":
        seq = system.get("sourceSequence")
        if isinstance(seq, int):
            return f"[Seq {seq}] {name}"
        return name

    return name


def make_item_doc(entry: dict) -> dict:
    system = entry["system"]
    pathway_id = system.get("pathwayId")

    sequence = None
    for key in ["sequence", "sourceSequence", "minSequence"]:
        value = system.get(key)
        if isinstance(value, int):
            sequence = value
            break

    return {
        "_id": stable_id(entry["id"]),
        "name": with_grouped_name(entry),
        "type": entry["itemType"],
        "img": entry.get("img", "icons/svg/item-bag.svg"),
        "system": system,
        "effects": system.get("effects", []),
        "folder": None,
        "sort": 0,
        "ownership": {"default": 0},
        "flags": {
            "lotm": {
                "contentId": entry["id"],
                "version": entry["version"],
                "minSystemVersion": entry["minSystemVersion"],
                "maxTestedSystemVersion": entry["maxTestedSystemVersion"],
                "dependencies": entry.get("dependencies", []),
                "groups": {
                    "pathwayId": pathway_id,
                    "sequence": sequence,
                    "itemType": entry["itemType"],
                    "pack": resolve_pack(entry),
                },
            }
        },
    }


def make_rolltable_doc(entry: dict) -> dict:
    results = []
    current = 1
    for index, result in enumerate(entry["results"]):
        weight = int(result.get("weight", 1))
        next_value = current + weight - 1
        results.append(
            {
                "_id": stable_id(f"{entry['id']}.result.{index + 1}"),
                "type": 0,
                "text": result["text"],
                "img": result.get("img", "icons/svg/d20-black.svg"),
                "weight": weight,
                "range": [current, next_value],
                "drawn": False,
                "documentCollection": None,
                "documentId": None,
                "flags": {},
            }
        )
        current = next_value + 1

    formula = entry.get("formula", f"1d{current - 1}")
    segment = infer_rolltable_segment(entry)

    return {
        "_id": stable_id(entry["id"]),
        "name": f"[{segment.title()}] {entry['name']}",
        "img": entry.get("img", "icons/svg/d20-black.svg"),
        "description": entry.get("description", ""),
        "results": results,
        "formula": formula,
        "replacement": True,
        "displayRoll": True,
        "folder": None,
        "sort": 0,
        "flags": {
            "lotm": {
                "contentId": entry["id"],
                "version": entry["version"],
                "minSystemVersion": entry["minSystemVersion"],
                "maxTestedSystemVersion": entry["maxTestedSystemVersion"],
                "dependencies": entry.get("dependencies", []),
                "groups": {
                    "segment": segment,
                    "pack": resolve_pack(entry),
                },
            }
        },
    }


def make_actor_doc(entry: dict) -> dict:
    actor_type = entry["actorType"]
    system = entry["system"]

    return {
        "_id": stable_id(entry["id"]),
        "name": entry["name"],
        "type": actor_type,
        "img": entry.get("img", "icons/svg/mystery-man.svg"),
        "system": system,
        "items": entry.get("items", []),
        "effects": entry.get("effects", []),
        "folder": None,
        "sort": 0,
        "ownership": {"default": 0},
        "prototypeToken": {
            "name": entry["name"],
            "actorLink": False,
            "appendNumber": False,
            "prependAdjective": False,
        },
        "flags": {
            "lotm": {
                "contentId": entry["id"],
                "version": entry["version"],
                "minSystemVersion": entry["minSystemVersion"],
                "maxTestedSystemVersion": entry["maxTestedSystemVersion"],
                "dependencies": entry.get("dependencies", []),
                "groups": {
                    "category": resolve_pack(entry),
                },
            }
        },
    }


def make_journal_doc(entry: dict) -> dict:
    pages = []
    for index, page in enumerate(entry["pages"]):
        pages.append(
            {
                "_id": stable_id(f"{entry['id']}.page.{index + 1}"),
                "name": page["title"],
                "type": "text",
                "text": {
                    "content": page["content"],
                    "format": int(page.get("format", 1)),
                },
                "sort": index * 10,
                "ownership": {"default": 0},
                "flags": {},
            }
        )

    return {
        "_id": stable_id(entry["id"]),
        "name": entry["name"],
        "pages": pages,
        "folder": None,
        "sort": 0,
        "ownership": {"default": 0},
        "flags": {
            "lotm": {
                "contentId": entry["id"],
                "version": entry["version"],
                "minSystemVersion": entry["minSystemVersion"],
                "maxTestedSystemVersion": entry["maxTestedSystemVersion"],
                "dependencies": entry.get("dependencies", []),
                "groups": {
                    "category": resolve_pack(entry),
                },
            }
        },
    }


def build_document(entry: dict) -> dict:
    doc_type = entry["documentType"]
    if doc_type == "Item":
        return make_item_doc(entry)
    if doc_type == "RollTable":
        return make_rolltable_doc(entry)
    if doc_type == "Actor":
        return make_actor_doc(entry)
    if doc_type == "JournalEntry":
        return make_journal_doc(entry)
    raise AssertionError(f"Unsupported document type in pack build: {doc_type}")


def clear_pack_outputs():
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    for path in PACKS_DIR.glob("*.db"):
        path.unlink()


def build_packs(entries):
    clear_pack_outputs()

    by_pack = {}
    for entry in entries:
        pack_name = resolve_pack(entry)
        by_pack.setdefault(pack_name, []).append(entry)

    outputs = []
    for pack_name in sorted(by_pack.keys()):
        docs = []
        for entry in sorted(by_pack[pack_name], key=lambda e: e["id"]):
            docs.append(build_document(entry))

        output_path = PACKS_DIR / f"{pack_name}.db"
        serialized = "\n".join(json.dumps(doc, ensure_ascii=True, separators=(",", ":")) for doc in docs) + "\n"
        output_path.write_text(serialized, encoding="utf-8")
        outputs.append((pack_name, output_path, len(docs)))

    return outputs


def main():
    entries, warnings = load_and_validate_content()
    outputs = build_packs(entries)

    if warnings:
        print("[pack-build] warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print("[pack-build] generated packs:")
    for pack_name, output_path, count in outputs:
        print(f"  - {pack_name}: {count} docs -> {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()