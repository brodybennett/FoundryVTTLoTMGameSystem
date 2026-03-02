import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = ROOT / "content-src"
SYSTEM_PATH = ROOT / "system.json"

ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
PACK_RE = re.compile(r"^[a-z][a-z0-9-]*$")
TAG_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
ROLLTABLE_SEGMENTS = {"resources", "abilities", "rituals", "artifacts", "corruption", "encounters"}
FORMULA_RE = re.compile(r"^1d([1-9][0-9]*)$")


ACTOR_ALLOWED_TYPES = {"character", "npc"}
JOURNAL_ALLOWED_FORMATS = {0, 1}


ITEM_BUCKET_TYPES = {"weapon", "armor", "gear", "feature", "consumable", "ingredient", "background"}


ACTOR_REQUIRED_PACKS = {
    "actors-factions",
    "actors-beyonder-monsters",
    "actors-civilians",
}


RULES_REQUIRED_PACK = "rules-reference"


def fail(message: str) -> None:
    raise AssertionError(message)


def parse_semver(value: str, label: str):
    if not isinstance(value, str):
        fail(f"{label} must be string semver")
    match = SEMVER_RE.fullmatch(value)
    if not match:
        fail(f"{label} must match X.Y.Z, got {value}")
    return tuple(int(part) for part in match.groups())


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


def validate_common_fields(entry, current_version, warnings):
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


def validate_item_entry(entry):
    content_id = entry["id"]
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


def validate_rolltable_entry(entry):
    content_id = entry["id"]
    segment = entry.get("segment")
    if not isinstance(segment, str) or segment not in ROLLTABLE_SEGMENTS:
        fail(f"{content_id}.segment must be one of {sorted(ROLLTABLE_SEGMENTS)}")

    formula = entry.get("formula")
    if not isinstance(formula, str):
        fail(f"{content_id}.formula is required and must be string")
    m = FORMULA_RE.fullmatch(formula)
    if m is None:
        fail(f"{content_id}.formula must match 1dN where N >= 1")

    results = entry.get("results")
    if not isinstance(results, list) or not results:
        fail(f"{content_id} rolltable must include non-empty results")

    seen_text = set()
    weighted_total = 0
    for idx, result in enumerate(results):
        if not isinstance(result, dict):
            fail(f"{content_id} result #{idx + 1} must be object")
        if not isinstance(result.get("text"), str) or not result.get("text"):
            fail(f"{content_id} result #{idx + 1} missing text")
        normalized_text = result["text"].strip().lower()
        if normalized_text in seen_text:
            fail(f"{content_id} has duplicate result text at #{idx + 1}")
        seen_text.add(normalized_text)
        weight = result.get("weight", 1)
        if not isinstance(weight, int) or weight < 1:
            fail(f"{content_id} result #{idx + 1} weight must be integer >=1")
        weighted_total += weight

    formula_sides = int(m.group(1))
    if formula_sides != weighted_total:
        fail(f"{content_id} formula {formula} is incoherent with weighted result total {weighted_total}")

    trigger_tags = entry.get("triggerTags", [])
    if trigger_tags is not None:
        if not isinstance(trigger_tags, list):
            fail(f"{content_id}.triggerTags must be an array when provided")
        for tag in trigger_tags:
            if not isinstance(tag, str) or TAG_RE.fullmatch(tag) is None:
                fail(f"{content_id} has invalid trigger tag: {tag}")


def validate_actor_entry(entry):
    content_id = entry["id"]
    actor_type = entry.get("actorType")
    if actor_type not in ACTOR_ALLOWED_TYPES:
        fail(f"{content_id}.actorType must be one of {sorted(ACTOR_ALLOWED_TYPES)}")
    if "system" not in entry or not isinstance(entry["system"], dict):
        fail(f"{content_id} actor entry missing system object")
    creation = entry["system"].get("creation")
    if not isinstance(creation, dict):
        fail(f"{content_id}.system.creation is required")
    state = creation.get("state")
    allowed_states = {"draft", "identity", "attributes", "skills", "pathway", "equipment", "complete"}
    if state not in allowed_states:
        fail(f"{content_id}.system.creation.state must be one of {sorted(allowed_states)}")
    completed = creation.get("completedSteps")
    if not isinstance(completed, list):
        fail(f"{content_id}.system.creation.completedSteps must be array")
    if creation.get("version") is None:
        fail(f"{content_id}.system.creation.version is required")


def validate_journal_entry(entry):
    content_id = entry["id"]
    pages = entry.get("pages")
    if not isinstance(pages, list) or not pages:
        fail(f"{content_id} journal entry must include non-empty pages array")

    for idx, page in enumerate(pages):
        if not isinstance(page, dict):
            fail(f"{content_id} page #{idx + 1} must be object")
        title = page.get("title")
        content = page.get("content")
        if not isinstance(title, str) or not title.strip():
            fail(f"{content_id} page #{idx + 1} missing title")
        if not isinstance(content, str) or not content.strip():
            fail(f"{content_id} page #{idx + 1} missing content")
        fmt = page.get("format", 1)
        if fmt not in JOURNAL_ALLOWED_FORMATS:
            fail(f"{content_id} page #{idx + 1} has invalid format {fmt}")


def validate_entry(entry, current_version, warnings):
    validate_common_fields(entry, current_version, warnings)

    doc_type = entry["documentType"]
    if doc_type == "Item":
        validate_item_entry(entry)
        return
    if doc_type == "RollTable":
        validate_rolltable_entry(entry)
        return
    if doc_type == "Actor":
        validate_actor_entry(entry)
        return
    if doc_type == "JournalEntry":
        validate_journal_entry(entry)
        return

    fail(f"{entry['id']} has unsupported documentType: {doc_type}")


def enforce_counts(entries):
    item_entries = [entry for entry in entries if entry["documentType"] == "Item"]

    ability_count = len([entry for entry in item_entries if entry.get("itemType") == "ability"])
    item_bucket_count = len([entry for entry in item_entries if entry.get("itemType") in ITEM_BUCKET_TYPES])
    ritual_count = len([entry for entry in item_entries if entry.get("itemType") == "ritual"])
    artifact_count = len([entry for entry in item_entries if entry.get("itemType") == "artifact"])
    rolltable_count = len([entry for entry in entries if entry["documentType"] == "RollTable"])

    if ability_count < 12:
        fail(f"Expected >=12 abilities, found {ability_count}")
    if item_bucket_count < 20:
        fail(f"Expected >=20 item bucket entries, found {item_bucket_count}")
    if ritual_count < 6:
        fail(f"Expected >=6 rituals, found {ritual_count}")
    if artifact_count < 4:
        fail(f"Expected >=4 artifacts, found {artifact_count}")
    if rolltable_count < 6:
        fail(f"Expected >=6 roll tables, found {rolltable_count}")

    if not any(entry["id"] == "pathway.seer" for entry in entries):
        fail("Required pathway.seer entry is missing")

    actor_packs = {entry["pack"] for entry in entries if entry["documentType"] == "Actor"}
    missing_actor_packs = sorted(ACTOR_REQUIRED_PACKS - actor_packs)
    if missing_actor_packs:
        fail(f"Missing actor category packs: {missing_actor_packs}")

    if not any(entry["documentType"] == "JournalEntry" and entry["pack"] == RULES_REQUIRED_PACK for entry in entries):
        fail("Missing rules-reference JournalEntry content")


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
    rolltable_schema = ROOT / "schemas" / "content.rolltable.schema.v1_2.json"
    if not rolltable_schema.exists():
        fail("Missing rolltable source schema: schemas/content.rolltable.schema.v1_2.json")
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
