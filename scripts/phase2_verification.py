import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(msg: str) -> None:
    raise AssertionError(msg)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_required_files():
    required = [
        ROOT / "system-config-v1.1.json",
        ROOT / "foundry-schema-v1.1.md",
        ROOT / "content-validation-rules-v1.1.md",
        ROOT / "phase2-test-matrix-v1.1.md",
        ROOT / "schemas" / "actor.system.schema.v1_1.json",
        ROOT / "schemas" / "item.system.schema.v1_1.json",
        ROOT / "schemas" / "effect.schema.v1_1.json",
        ROOT / "schemas" / "content.pack.manifest.schema.v1_1.json",
        ROOT / "data" / "skills.registry.v1.1.json",
        ROOT / "data" / "conditions.library.v1.1.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        fail(f"Missing phase 2 file(s): {missing}")


def check_config_contract():
    cfg = load_json(ROOT / "system-config-v1.1.json")
    if cfg.get("contractVersion") != "1.1.0":
        fail("system-config-v1.1.json must set contractVersion=1.1.0")

    registry = cfg.get("contentRegistry", {})
    if registry.get("skillsFile") != "data/skills.registry.v1.1.json":
        fail("contentRegistry.skillsFile mismatch")
    if registry.get("conditionsFile") != "data/conditions.library.v1.1.json":
        fail("contentRegistry.conditionsFile mismatch")

    whitelist = cfg.get("validation", {}).get("effectPathWhitelist", [])
    if not whitelist or not all(p.startswith("system.") for p in whitelist):
        fail("validation.effectPathWhitelist must contain system.* prefixes")

    scopes = set(cfg.get("usageLimits", {}).get("defaultScopes", []))
    needed = {"perTurn", "perRound", "perScene", "perShortRest", "perLongRest"}
    if not needed.issubset(scopes):
        fail("usageLimits.defaultScopes missing required scopes")

    ritual_formula = cfg.get("formulaRegistry", {}).get("check.ritual.v1", "")
    if "- corruptionPenalty" in ritual_formula:
        fail("check.ritual.v1 must not subtract a negative corruptionPenalty")

    return cfg


def check_skill_registry():
    data = load_json(ROOT / "data" / "skills.registry.v1.1.json")
    skills = {s["id"]: s["linkedAttr"] for s in data.get("skills", [])}
    expected = {
        "ritualism": "wil",
        "investigation": "int",
        "perception": "int",
        "insight": "wil",
        "persuasion": "cha",
        "deception": "cha",
        "intimidation": "cha",
        "etiquette": "cha",
        "willpower": "wil",
        "endurance": "con",
        "medicine": "int",
        "occult": "int",
        "athletics": "str",
        "melee": "str",
        "firearms": "dex",
        "stealth": "dex",
        "acrobatics": "dex",
        "streetwise": "int",
        "commerce": "int",
        "crafting": "int",
    }
    if skills != expected:
        fail("skills.registry.v1.1.json does not match canonical skill map")


def check_schema_ids_and_contracts():
    actor = load_json(ROOT / "schemas" / "actor.system.schema.v1_1.json")
    item = load_json(ROOT / "schemas" / "item.system.schema.v1_1.json")
    effect = load_json(ROOT / "schemas" / "effect.schema.v1_1.json")
    manifest = load_json(ROOT / "schemas" / "content.pack.manifest.schema.v1_1.json")

    if actor.get("$id") != "lotm/actor.system.schema.v1_1.json":
        fail("actor v1.1 schema $id mismatch")
    if item.get("$id") != "lotm/item.system.schema.v1_1.json":
        fail("item v1.1 schema $id mismatch")
    if effect.get("$id") != "lotm/effect.schema.v1_1.json":
        fail("effect v1.1 schema $id mismatch")
    if manifest.get("$id") != "lotm/content.pack.manifest.schema.v1_1.json":
        fail("manifest v1.1 schema $id mismatch")

    track_props = set(actor["properties"]["tracks"]["properties"].keys())
    required_track_props = {
        "actionLock",
        "movementCheckPenalty",
        "damageOutMultiplier",
        "incomingOffenseBonus",
        "offensePenaltyVsSource",
        "verbalLocked",
        "markedBySourceBonus",
        "isDowned",
    }
    if not required_track_props.issubset(track_props):
        missing = sorted(required_track_props - track_props)
        fail(f"actor schema missing condition-driven track fields: {missing}")

    root_required = set(item.get("required", []))
    if "dependencies" not in root_required:
        fail("item schema must require dependencies on all items")

    formula_key = item.get("properties", {}).get("formulaKey", {})
    if "enum" in formula_key:
        fail("item.schema formulaKey must be registry-driven, not enum-locked")

    effect_required = set(effect.get("required", []))
    if "sourceCategory" not in effect_required:
        fail("effect schema must require sourceCategory")

    path_pattern = manifest["properties"]["entries"]["items"]["properties"]["path"].get("pattern", "")
    if r"\.\." not in path_pattern:
        fail("manifest path rule must block path traversal")


MANIFEST_PATH_RE = re.compile(r"^(?![A-Za-z]:)(?!/)(?!\\\\)(?!.*\.\.)[a-zA-Z0-9_./-]+$")


def validate_effect_semantics(effect_obj, whitelist_prefixes):
    errors = []
    save_type = effect_obj.get("saveType")
    save_target = effect_obj.get("saveTarget")
    remove_on = effect_obj.get("removeOn", [])

    path = effect_obj.get("path")
    if path and not any(path.startswith(prefix) for prefix in whitelist_prefixes):
        errors.append("path_not_whitelisted")

    if "sourceCategory" not in effect_obj:
        errors.append("missing_sourceCategory")

    if save_type == "none":
        if save_target != 0:
            errors.append("save_none_target_must_be_zero")
        if "saveSuccess" in remove_on:
            errors.append("save_none_cannot_remove_on_save_success")
    else:
        if not isinstance(save_target, int) or not (1 <= save_target <= 95):
            errors.append("save_target_must_be_1_95_when_save_enabled")

    if effect_obj.get("op") == "cost" and effect_obj.get("value", 0) < 0:
        errors.append("cost_must_be_non_negative")

    return errors


def validate_item_semantics(item_obj, formula_keys):
    errors = []

    if "dependencies" not in item_obj:
        errors.append("missing_dependencies")

    if item_obj.get("type") == "ability":
        seq = item_obj.get("sequence")
        min_seq = item_obj.get("minSequence")
        if isinstance(seq, int) and isinstance(min_seq, int) and min_seq > seq:
            errors.append("ability_minSequence_gt_sequence")

        allowed = item_obj.get("allowedPathwayIds")
        pathway = item_obj.get("pathwayId")
        if pathway and isinstance(allowed, list) and pathway not in allowed:
            errors.append("allowedPathwayIds_missing_pathwayId")

        key = item_obj.get("formulaKey")
        if key and key not in formula_keys:
            errors.append("unknown_formula_key")

    return errors


def validate_manifest(manifest):
    required = {
        "packId",
        "packVersion",
        "schemaTarget",
        "minSystemVersion",
        "maxTestedSystemVersion",
        "entries",
        "dependencies",
    }
    missing = required - set(manifest.keys())
    if missing:
        return False, f"missing_keys={sorted(missing)}"

    if manifest["schemaTarget"] not in {"v1", "v1.1"}:
        return False, "invalid_schema_target"

    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) < 1:
        return False, "entries_must_be_non_empty_list"

    ids = [e.get("id") for e in entries]
    if len(ids) != len(set(ids)):
        return False, "duplicate_entry_ids"

    paths = [e.get("path") for e in entries]
    if len(paths) != len(set(paths)):
        return False, "duplicate_entry_paths"

    for path in paths:
        if not isinstance(path, str) or not MANIFEST_PATH_RE.fullmatch(path):
            return False, "unsafe_entry_path"

    return True, "ok"


def check_conditions_library(whitelist_prefixes, actor_track_props):
    library = load_json(ROOT / "data" / "conditions.library.v1.1.json")
    conditions = library.get("conditions", [])
    required_ids = {
        "condition.stunned",
        "condition.restrained",
        "condition.weakened",
        "condition.exposed",
        "condition.frightened",
        "condition.silenced",
        "condition.marked",
        "condition.bleeding",
        "condition.burning",
        "condition.downed",
    }
    got = {c.get("id") for c in conditions}
    if got != required_ids:
        fail("conditions library IDs do not match canonical set")

    req_keys = {
        "id",
        "op",
        "sourceCategory",
        "applyPhase",
        "tickPhase",
        "durationRounds",
        "saveType",
        "saveTarget",
        "stackRule",
        "removeOn",
    }

    for condition in conditions:
        effects = condition.get("effects", [])
        if not effects:
            fail(f"Condition has no effects: {condition.get('id')}")
        for effect_obj in effects:
            missing = sorted(req_keys - set(effect_obj.keys()))
            if missing:
                fail(f"Condition effect missing keys {missing}: {effect_obj.get('id')}")

            errs = validate_effect_semantics(effect_obj, whitelist_prefixes)
            if errs:
                fail(f"Condition effect semantic errors {errs}: {effect_obj.get('id')}")

            path = effect_obj.get("path")
            if path and path.startswith("system.tracks."):
                root_field = path.split(".", 2)[2].split(".", 1)[0]
                if root_field not in actor_track_props:
                    fail(f"Condition effect path targets undefined actor.tracks field: {path}")


def check_item_semantic_rules(cfg):
    formula_keys = set(cfg["formulaRegistry"].keys())

    valid_ability = {
        "id": "ability.test.valid",
        "schemaVersion": 1,
        "name": "Valid Ability",
        "type": "ability",
        "pathwayId": "pathway.seer",
        "allowedPathwayIds": ["pathway.seer"],
        "sequence": 7,
        "minSequence": 6,
        "activation": "action",
        "resource": "spirit",
        "cost": 4,
        "cooldown": 1,
        "formulaKey": "check.skill.v1",
        "effects": [],
        "dependencies": {
            "minSystemVersion": "1.1.0",
            "maxTestedSystemVersion": "1.1.0"
        }
    }
    if validate_item_semantics(valid_ability, formula_keys):
        fail("Valid ability failed semantic validation")

    bad_min_seq = dict(valid_ability)
    bad_min_seq["id"] = "ability.test.bad_seq"
    bad_min_seq["minSequence"] = 8
    errs = validate_item_semantics(bad_min_seq, formula_keys)
    if "ability_minSequence_gt_sequence" not in errs:
        fail("minSequence > sequence should fail semantic validation")

    bad_allowed = dict(valid_ability)
    bad_allowed["id"] = "ability.test.bad_allowed"
    bad_allowed["allowedPathwayIds"] = ["pathway.spectator"]
    errs = validate_item_semantics(bad_allowed, formula_keys)
    if "allowedPathwayIds_missing_pathwayId" not in errs:
        fail("allowedPathwayIds missing pathwayId should fail semantic validation")

    missing_deps = dict(valid_ability)
    missing_deps["id"] = "ability.test.missing_deps"
    missing_deps.pop("dependencies")
    errs = validate_item_semantics(missing_deps, formula_keys)
    if "missing_dependencies" not in errs:
        fail("missing dependencies should fail semantic validation")

    bad_formula = dict(valid_ability)
    bad_formula["id"] = "ability.test.bad_formula"
    bad_formula["formulaKey"] = "check.custom.future_formula"
    errs = validate_item_semantics(bad_formula, formula_keys)
    if "unknown_formula_key" not in errs:
        fail("Unknown formula key should fail semantic validation")


def check_manifest_rules():
    valid_manifest = {
        "packId": "pack.core.test",
        "packVersion": "1.1.0",
        "schemaTarget": "v1.1",
        "minSystemVersion": "1.1.0",
        "maxTestedSystemVersion": "1.1.0",
        "entries": [
            {
                "id": "ability.seer.hunch_of_danger",
                "type": "ability",
                "path": "packs/ability.seer.hunch_of_danger.json",
            },
            {
                "id": "condition.stunned",
                "type": "conditionTemplate",
                "path": "packs/condition.stunned.json",
            },
        ],
        "dependencies": [],
    }
    ok, why = validate_manifest(valid_manifest)
    if not ok:
        fail(f"Valid manifest failed: {why}")

    invalid_schema = dict(valid_manifest)
    invalid_schema["schemaTarget"] = "v2"
    ok, why = validate_manifest(invalid_schema)
    if ok or why != "invalid_schema_target":
        fail("Invalid schema target test did not fail")

    invalid_empty = dict(valid_manifest)
    invalid_empty["entries"] = []
    ok, why = validate_manifest(invalid_empty)
    if ok or why != "entries_must_be_non_empty_list":
        fail("Empty entries test did not fail")

    invalid_dup_id = dict(valid_manifest)
    invalid_dup_id["entries"] = [
        {"id": "ability.seer.hunch_of_danger", "type": "ability", "path": "packs/a.json"},
        {"id": "ability.seer.hunch_of_danger", "type": "ability", "path": "packs/b.json"},
    ]
    ok, why = validate_manifest(invalid_dup_id)
    if ok or why != "duplicate_entry_ids":
        fail("Duplicate manifest ID test did not fail")

    invalid_dup_path = dict(valid_manifest)
    invalid_dup_path["entries"] = [
        {"id": "ability.seer.hunch_of_danger", "type": "ability", "path": "packs/shared.json"},
        {"id": "ability.seer.foresight", "type": "ability", "path": "packs/shared.json"},
    ]
    ok, why = validate_manifest(invalid_dup_path)
    if ok or why != "duplicate_entry_paths":
        fail("Duplicate manifest path test did not fail")

    invalid_unsafe_path = dict(valid_manifest)
    invalid_unsafe_path["entries"] = [
        {"id": "ability.seer.hunch_of_danger", "type": "ability", "path": "../secrets.json"}
    ]
    ok, why = validate_manifest(invalid_unsafe_path)
    if ok or why != "unsafe_entry_path":
        fail("Unsafe manifest path test did not fail")


def main():
    print("[phase2] checking required files")
    ensure_required_files()

    print("[phase2] checking config contract")
    cfg = check_config_contract()

    print("[phase2] checking schema identifiers and hardening contracts")
    check_schema_ids_and_contracts()

    print("[phase2] checking skills registry")
    check_skill_registry()

    actor = load_json(ROOT / "schemas" / "actor.system.schema.v1_1.json")
    track_props = set(actor["properties"]["tracks"]["properties"].keys())

    print("[phase2] checking conditions library")
    check_conditions_library(cfg["validation"]["effectPathWhitelist"], track_props)

    print("[phase2] checking item semantic rules")
    check_item_semantic_rules(cfg)

    print("[phase2] checking manifest rules")
    check_manifest_rules()

    print("ALL PHASE 2 CHECKS PASSED")


if __name__ == "__main__":
    main()
