import hashlib
import json
from pathlib import Path

from validate_content_source import ROOT, load_and_validate_content

PACKS_DIR = ROOT / "packs"


def stable_id(content_id: str) -> str:
    return hashlib.md5(content_id.encode("utf-8")).hexdigest()[:16]


def make_item_doc(entry: dict) -> dict:
    system = entry["system"]
    return {
        "_id": stable_id(entry["id"]),
        "name": entry["name"],
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

    return {
        "_id": stable_id(entry["id"]),
        "name": entry["name"],
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
            }
        },
    }


def build_packs(entries):
    by_pack = {}
    for entry in entries:
        by_pack.setdefault(entry["pack"], []).append(entry)

    PACKS_DIR.mkdir(parents=True, exist_ok=True)

    outputs = []
    for pack_name in sorted(by_pack.keys()):
        docs = []
        for entry in sorted(by_pack[pack_name], key=lambda e: e["id"]):
            if entry["documentType"] == "Item":
                docs.append(make_item_doc(entry))
            elif entry["documentType"] == "RollTable":
                docs.append(make_rolltable_doc(entry))
            else:
                raise AssertionError(f"Unsupported document type in pack build: {entry['documentType']}")

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