import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = ROOT / "content-src"
SYSTEM_PATH = ROOT / "system.json"

ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
PACK_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def fail(message: str) -> None:
    raise AssertionError(message)


def parse_semver(value: str, label: str):
    if not isinstance(value, str):
        fail(f"{label} must be string semver")
    match = SEMVER_RE.fullmatch(value)
    if not match:
        fail(f"{label} must match X.Y.Z, got {value}")
    return tuple(int(part) for part in match.groups())


def semver_compare(a, b):
    return (a > b) - (a < b)


def load_system_version():
    if not SYSTEM_PATH.exists():
        fail("system.json is missing")
    payload = json.loads(SYSTEM_PATH.read_text(encoding="utf-8"))
    version = payload.get("version")
    return parse_semver(version, "system.version")


def load_entries():
    if not CONTENT_ROOT.exists():
        fail("content-src directory is missing")

    entries = []
    for path in sorted(CONTENT_ROOT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_entries = data.get("entries")
        if not isinstance(raw_entries, list):
            fail(f"{path.relative_to(ROOT)} must define entries array")
        for entry in raw_entries:
            if not isinstance(entry, dict):
                fail(f"Entry in {path.relative_to(ROOT)} must be object")
            tagged = dict(entry)
            tagged["__source"] = str(path.relative_to(ROOT))
            entries.append(tagged)
    return entries


def validate_entry(entry, current_version, warnings):
    required = {
        "id",
        "pack",
        "documentType",
        "name",
        "version",
        "minSystemVersion",
        "maxTestedSystemVersion",
        "dependencies",
    }
    missing = sorted(required - set(entry.keys()))
    if missing:
        fail(f"{entry.get('__source', '<unknown>')} missing entry keys: {missing}")

    content_id = entry["id"]
    if ID_RE.fullmatch(content_id) is None:
        fail(f"Invalid content id: {content_id}")

    pack = entry["pack"]
    if PACK_RE.fullmatch(pack) is None:
        fail(f"Invalid pack name for {content_id}: {pack}")

    version = parse_semver(entry["version"], f"{content_id}.version")
    min_v = parse_semver(entry["minSystemVersion"], f"{content_id}.minSystemVersion")
    max_v = parse_semver(entry["maxTestedSystemVersion"], f"{content_id}.maxTestedSystemVersion")

    if min_v > max_v:
        fail(f"{content_id} has minSystemVersion > maxTestedSystemVersion")
    if min_v > current_version:
        fail(f"{content_id} requires newer system than current version")
    if current_version > max_v:
        warnings.append(f"{content_id} tested only up to {entry['maxTestedSystemVersion']}")

    if version < min_v:
        fail(f"{content_id} version cannot be lower than minSystemVersion")

    dependencies = entry["dependencies"]
    if not isinstance(dependencies, list):
        fail(f"{content_id}.dependencies must be an array")
    for dep in dependencies:
        if not isinstance(dep, str) or ID_RE.fullmatch(dep) is None:
            fail(f"{content_id} has invalid dependency id: {dep}")

    doc_type = entry["documentType"]
    if doc_type not in {"Item", "RollTable"}:
        fail(f"{content_id} has unsupported documentType: {doc_type}")

    if doc_type == "Item":
        if "itemType" not in entry:
            fail(f"{content_id} missing itemType")
        if "system" not in entry or not isinstance(entry["system"], dict):
            fail(f"{content_id} missing system object")
        system = entry["system"]
        if system.get("id") != content_id:
            fail(f"{content_id} system.id must match content id")
        if "dependencies" not in system or not isinstance(system["dependencies"], dict):
            fail(f"{content_id} system.dependencies must exist")
        dep_block = system["dependencies"]
        parse_semver(dep_block.get("minSystemVersion", ""), f"{content_id}.system.dependencies.minSystemVersion")
        parse_semver(dep_block.get("maxTestedSystemVersion", ""), f"{content_id}.system.dependencies.maxTestedSystemVersion")
        requires_ids = dep_block.get("requiresIds", [])
        if not isinstance(requires_ids, list):
            fail(f"{content_id}.system.dependencies.requiresIds must be array")
    else:
        results = entry.get("results")
        if not isinstance(results, list) or not results:
            fail(f"{content_id} rolltable must include non-empty results")
        for idx, result in enumerate(results):
            if not isinstance(result, dict):
                fail(f"{content_id} result #{idx + 1} must be object")
            if not isinstance(result.get("text"), str) or not result.get("text"):
                fail(f"{content_id} result #{idx + 1} missing text")
            weight = result.get("weight", 1)
            if not isinstance(weight, int) or weight < 1:
                fail(f"{content_id} result #{idx + 1} weight must be integer >=1")


def enforce_counts(entries):
    def count_items(pack, item_type=None):
        filtered = [
            e
            for e in entries
            if e["documentType"] == "Item" and e["pack"] == pack and (item_type is None or e.get("itemType") == item_type)
        ]
        return len(filtered)

    ability_count = count_items("seer-abilities", "ability")
    item_count = count_items("seer-items")
    ritual_count = count_items("seer-rituals", "ritual")
    artifact_count = count_items("seer-artifacts", "artifact")
    rolltable_count = len([e for e in entries if e["documentType"] == "RollTable" and e["pack"] == "seer-rolltables"])

    if ability_count < 12:
        fail(f"Expected >=12 abilities in seer-abilities pack, found {ability_count}")
    if item_count < 20:
        fail(f"Expected >=20 items in seer-items pack, found {item_count}")
    if ritual_count < 6:
        fail(f"Expected >=6 rituals in seer-rituals pack, found {ritual_count}")
    if artifact_count < 4:
        fail(f"Expected >=4 artifacts in seer-artifacts pack, found {artifact_count}")
    if rolltable_count < 6:
        fail(f"Expected >=6 roll tables in seer-rolltables pack, found {rolltable_count}")

    if not any(entry["id"] == "pathway.seer" for entry in entries):
        fail("Required pathway.seer entry is missing")


def validate_dependencies(entries):
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        fail("Duplicate content IDs detected across content-src")

    id_set = set(ids)

    for entry in entries:
        for dep in entry.get("dependencies", []):
            if dep not in id_set:
                fail(f"{entry['id']} references missing dependency {dep}")

        if entry["documentType"] == "Item":
            for dep in entry["system"]["dependencies"].get("requiresIds", []):
                if dep not in id_set:
                    fail(f"{entry['id']} system.dependencies.requiresIds references missing {dep}")


def load_and_validate_content():
    warnings = []
    current_version = load_system_version()
    entries = load_entries()

    if not entries:
        fail("No content entries found under content-src")

    for entry in entries:
        validate_entry(entry, current_version, warnings)

    validate_dependencies(entries)
    enforce_counts(entries)

    return entries, warnings


def main():
    entries, warnings = load_and_validate_content()
    if warnings:
        print("[content-validate] warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    print(f"[content-validate] PASS ({len(entries)} entries)")


if __name__ == "__main__":
    main()