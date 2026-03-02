import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
MANIFEST_PATH_RE = re.compile(r"^(?![A-Za-z]:)(?!/)(?!\\\\)(?!.*\.\.)[a-zA-Z0-9_./-]+$")
VALID_LINKED_ATTRS = {"str", "dex", "wil", "con", "cha", "int", "luck"}
BALANCE_GATE_MODES = {"warn", "strict", "off"}
ROLLTABLE_SEGMENTS = {"resources", "abilities", "rituals", "artifacts", "corruption", "encounters"}
ROLLTABLE_FORMULA_RE = re.compile(r"^1d([1-9][0-9]*)$")


def fail(msg: str) -> None:
    raise AssertionError(msg)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_semver(value: str, label: str):
    if not isinstance(value, str):
        fail(f"{label} must be a string semver, got {type(value).__name__}")
    m = SEMVER_RE.fullmatch(value)
    if m is None:
        fail(f"{label} is not valid semver X.Y.Z: {value}")
    return tuple(int(part) for part in m.groups())


def ensure_semver_window(min_version: str, max_version: str, current_version, label: str, warnings):
    min_v = parse_semver(min_version, f"{label}.minSystemVersion")
    max_v = parse_semver(max_version, f"{label}.maxTestedSystemVersion")
    if min_v > max_v:
        fail(f"{label} has minSystemVersion > maxTestedSystemVersion")
    if min_v > current_version:
        fail(f"{label} requires newer system than current configVersion")
    if current_version > max_v:
        warnings.append(f"{label} tested only up to {max_version}, current is {'.'.join(map(str, current_version))}")


def ensure_required_files():
    required = [
        ROOT / "system-config-v1.1.json",
        ROOT / "foundry-schema-v1.1.md",
        ROOT / "content-validation-rules-v1.1.md",
        ROOT / "phase2-test-matrix-v1.1.md",
        ROOT / "core-tables-v1.csv",
        ROOT / "schemas" / "actor.system.schema.v1_1.json",
        ROOT / "schemas" / "item.system.schema.v1_1.json",
        ROOT / "schemas" / "effect.schema.v1_1.json",
        ROOT / "schemas" / "content.pack.manifest.schema.v1_1.json",
        ROOT / "schemas" / "content.rolltable.schema.v1_2.json",
        ROOT / "data" / "skills.registry.v1.1.json",
        ROOT / "data" / "conditions.library.v1.1.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        fail(f"Missing phase 2 file(s): {missing}")


def resolve_balance_gate_mode(cfg, cli_mode):
    configured = cfg.get("validation", {}).get("gates", {}).get("balanceGateMode", "warn")
    mode = cli_mode or configured or "warn"
    if mode not in BALANCE_GATE_MODES:
        fail(f"Invalid balance gate mode: {mode}. Allowed={sorted(BALANCE_GATE_MODES)}")
    return mode


def check_config_contract(cli_balance_mode):
    cfg = load_json(ROOT / "system-config-v1.1.json")
    if cfg.get("contractVersion") != "1.1.0":
        fail("system-config-v1.1.json must set contractVersion=1.1.0")
    current_version = parse_semver(cfg.get("configVersion", ""), "system-config.configVersion")

    registry = cfg.get("contentRegistry", {})
    if registry.get("skillsFile") != "data/skills.registry.v1.1.json":
        fail("contentRegistry.skillsFile mismatch")
    if registry.get("conditionsFile") != "data/conditions.library.v1.1.json":
        fail("contentRegistry.conditionsFile mismatch")

    corruption = cfg.get("corruption", {})
    if corruption.get("maxUniversalPenalty") != -10:
        fail("corruption.maxUniversalPenalty must be -10 in Phase 2")
    if corruption.get("eventTriggersPct") != [30, 60, 90, 100]:
        fail("corruption.eventTriggersPct must remain [30, 60, 90, 100]")

    expected_bands = [
        {"startPct": 0, "endPct": 9, "penalty": 0},
        {"startPct": 10, "endPct": 19, "penalty": -1},
        {"startPct": 20, "endPct": 29, "penalty": -2},
        {"startPct": 30, "endPct": 39, "penalty": -3},
        {"startPct": 40, "endPct": 49, "penalty": -4},
        {"startPct": 50, "endPct": 59, "penalty": -5},
        {"startPct": 60, "endPct": 69, "penalty": -6},
        {"startPct": 70, "endPct": 79, "penalty": -7},
        {"startPct": 80, "endPct": 89, "penalty": -8},
        {"startPct": 90, "endPct": 100, "penalty": -10},
    ]
    if corruption.get("penaltyBands") != expected_bands:
        fail("corruption.penaltyBands must match canonical Phase 2 band table")

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
    if "/9" not in ritual_formula or "/3" in ritual_formula:
        fail("check.ritual.v1 must use attribute divisor /9 and not /3")
    corruption_formula = cfg.get("formulaRegistry", {}).get("calc.corruption.penalty.v1", "")
    if "lookupBandPenalty" not in corruption_formula:
        fail("calc.corruption.penalty.v1 must reference band lookup semantics")

    channeling = cfg.get("advancement", {}).get("channelingSelection", {})
    if channeling.get("defaultSkill") != "willpower" or channeling.get("alternateSkill") != "endurance":
        fail("advancement.channelingSelection must define willpower default and endurance alternate")
    if channeling.get("declareBeforeRoll") is not True:
        fail("advancement.channelingSelection.declareBeforeRoll must be true")

    rolltable_hooks = cfg.get("automation", {}).get("rolltableHooks", {})
    expected_hooks = {
        "ritualFailure": "rituals",
        "artifactBacklash": "artifacts",
        "corruptionThresholdCross": "corruption",
    }
    for hook_name, expected_segment in expected_hooks.items():
        got_segment = rolltable_hooks.get(hook_name, {}).get("segment")
        if got_segment != expected_segment:
            fail(f"automation.rolltableHooks.{hook_name}.segment must be '{expected_segment}'")
    unknown_segments = {
        hook_name: hook_cfg.get("segment")
        for hook_name, hook_cfg in rolltable_hooks.items()
        if hook_cfg.get("segment") not in ROLLTABLE_SEGMENTS
    }
    if unknown_segments:
        fail(f"automation.rolltableHooks contains invalid segments: {unknown_segments}")

    balance_mode = resolve_balance_gate_mode(cfg, cli_balance_mode)
    return cfg, current_version, balance_mode


def check_skill_registry():
    data = load_json(ROOT / "data" / "skills.registry.v1.1.json")
    skills_raw = data.get("skills", [])
    if not isinstance(skills_raw, list) or not skills_raw:
        fail("skills.registry.v1.1.json must contain non-empty skills list")

    ids = [entry.get("id") for entry in skills_raw]
    if len(ids) != len(set(ids)):
        fail("skills.registry.v1.1.json contains duplicate skill ids")

    for entry in skills_raw:
        skill_id = entry.get("id")
        linked_attr = entry.get("linkedAttr")
        if not isinstance(skill_id, str) or ID_RE.fullmatch(skill_id) is None:
            fail(f"Invalid skill id format in registry: {skill_id}")
        if linked_attr not in VALID_LINKED_ATTRS:
            fail(f"Invalid linkedAttr for skill {skill_id}: {linked_attr}")

    skills = {entry["id"]: entry["linkedAttr"] for entry in skills_raw}
    canonical = {
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
    missing = sorted(set(canonical.keys()) - set(skills.keys()))
    if missing:
        fail(f"skills.registry.v1.1.json missing canonical skill IDs: {missing}")
    mismatched = [k for k, v in canonical.items() if skills.get(k) != v]
    if mismatched:
        fail(f"skills.registry.v1.1.json canonical linkedAttr mismatch: {mismatched}")


def check_schema_ids_and_contracts():
    actor = load_json(ROOT / "schemas" / "actor.system.schema.v1_1.json")
    item = load_json(ROOT / "schemas" / "item.system.schema.v1_1.json")
    effect = load_json(ROOT / "schemas" / "effect.schema.v1_1.json")
    manifest = load_json(ROOT / "schemas" / "content.pack.manifest.schema.v1_1.json")
    rolltable = load_json(ROOT / "schemas" / "content.rolltable.schema.v1_2.json")

    if actor.get("$id") != "lotm/actor.system.schema.v1_1.json":
        fail("actor v1.1 schema $id mismatch")
    if item.get("$id") != "lotm/item.system.schema.v1_1.json":
        fail("item v1.1 schema $id mismatch")
    if effect.get("$id") != "lotm/effect.schema.v1_1.json":
        fail("effect v1.1 schema $id mismatch")
    if manifest.get("$id") != "lotm/content.pack.manifest.schema.v1_1.json":
        fail("manifest v1.1 schema $id mismatch")
    if rolltable.get("$id") != "lotm/content.rolltable.schema.v1_2.json":
        fail("rolltable v1.2 schema $id mismatch")

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

    resource_required = set(actor["properties"]["resources"]["required"])
    if "deathSaves" not in resource_required:
        fail("actor schema resources must require deathSaves")
    if "creation" not in set(actor.get("required", [])):
        fail("actor schema must require creation contract")

    combat = actor["properties"].get("combat", {})
    combat_props = set(combat.get("properties", {}).keys())
    needed_combat = {"armor", "cover", "encumbrancePenalty", "damageReduction", "actionBudget"}
    if not needed_combat.issubset(combat_props):
        fail("actor schema combat contract missing required combat fields")

    root_required = set(item.get("required", []))
    if "dependencies" not in root_required:
        fail("item schema must require dependencies on all items")

    formula_key = item.get("properties", {}).get("formulaKey", {})
    if "enum" in formula_key:
        fail("item.schema formulaKey must be registry-driven, not enum-locked")

    effect_required = set(effect.get("required", []))
    if "sourceCategory" not in effect_required:
        fail("effect schema must require sourceCategory")
    if "target" not in effect_required or "trigger" not in effect_required:
        fail("effect schema must require target and trigger")

    path_pattern = manifest["properties"]["entries"]["items"]["properties"]["path"].get("pattern", "")
    if r"\.\." not in path_pattern:
        fail("manifest path rule must block path traversal")

    segment_enum = set(rolltable.get("properties", {}).get("segment", {}).get("enum", []))
    if segment_enum != ROLLTABLE_SEGMENTS:
        fail("rolltable schema segment enum must match canonical rolltable segments")


def load_core_tables():
    rows = []
    with (ROOT / "core-tables-v1.csv").open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows


def resolve_corruption_penalty(corruption_pct, penalty_bands):
    pct = float(corruption_pct)
    for band in penalty_bands:
        if float(band["startPct"]) <= pct <= float(band["endPct"]):
            return int(band["penalty"])
    fail(f"No corruption penalty band found for corruption={corruption_pct}")


def run_corruption_boundary_checks(cfg):
    boundaries = {59: -5, 60: -6, 69: -6, 70: -7, 89: -8, 90: -10, 100: -10}
    bands = cfg["corruption"]["penaltyBands"]
    for pct, expected in boundaries.items():
        got = resolve_corruption_penalty(pct, bands)
        if got != expected:
            fail(f"Corruption boundary mismatch at {pct}%: got {got}, expected {expected}")


def check_rolltable_source_contract():
    path = ROOT / "content-src" / "rolltables" / "seer.tables.json"
    data = load_json(path)
    entries = data.get("entries", [])
    if not isinstance(entries, list) or not entries:
        fail("rolltable source must contain non-empty entries array")

    segment_seen = set()
    for entry in entries:
        entry_id = entry.get("id", "<unknown>")
        segment = entry.get("segment")
        if segment not in ROLLTABLE_SEGMENTS:
            fail(f"rolltable {entry_id} has invalid segment: {segment}")
        segment_seen.add(segment)

        formula = entry.get("formula", "")
        m = ROLLTABLE_FORMULA_RE.fullmatch(formula)
        if m is None:
            fail(f"rolltable {entry_id} formula must match 1dN")
        sides = int(m.group(1))

        results = entry.get("results", [])
        if not results:
            fail(f"rolltable {entry_id} must include results")

        weighted_total = 0
        seen_text = set()
        for result in results:
            text = result.get("text")
            if not isinstance(text, str) or not text.strip():
                fail(f"rolltable {entry_id} includes result with empty text")
            normalized = text.strip().lower()
            if normalized in seen_text:
                fail(f"rolltable {entry_id} contains duplicate result text: {text}")
            seen_text.add(normalized)

            weight = result.get("weight")
            if not isinstance(weight, int) or weight < 1:
                fail(f"rolltable {entry_id} has invalid result weight: {weight}")
            weighted_total += weight

        if sides != weighted_total:
            fail(
                f"rolltable {entry_id} formula/result mismatch: formula sides={sides}, weighted_total={weighted_total}"
            )

        trigger_tags = entry.get("triggerTags", [])
        if not isinstance(trigger_tags, list):
            fail(f"rolltable {entry_id} triggerTags must be array")
        for tag in trigger_tags:
            if not isinstance(tag, str) or ID_RE.fullmatch(tag) is None:
                fail(f"rolltable {entry_id} has invalid trigger tag: {tag}")

    if segment_seen != ROLLTABLE_SEGMENTS:
        fail(
            f"rolltable source must include all canonical segments; missing={sorted(ROLLTABLE_SEGMENTS - segment_seen)}"
        )


def compute_progressed_attributes(cfg):
    seq_order = [int(v) for v in cfg["sequence"]["order"]]
    seq_map = cfg["sequence"]["map"]
    growth_rates = cfg["growth"]["attribute"]["rateByTier"]
    base = int(cfg["growth"]["attribute"]["anchorMin"])
    attrs = {k: base for k in ["str", "dex", "wil", "con", "cha", "int", "luck"]}
    by_seq = {seq_order[0]: dict(attrs)}

    for seq in seq_order[1:]:
        tier = seq_map[str(seq)]["tier"]
        rate = float(growth_rates[tier])
        attrs = {k: int(round(v * rate)) for k, v in attrs.items()}
        by_seq[seq] = dict(attrs)
    return by_seq


def compute_derived_hp_spirit(cfg, sequence, attrs):
    seq_meta = cfg["sequence"]["map"][str(sequence)]
    tier = seq_meta["tier"]
    idx = int(seq_meta["withinTierIndex"])

    health = cfg["derived"]["health"]
    spirit = cfg["derived"]["spirit"]
    health_mult = float(health["tierBase"][tier]) * pow(float(health["tierStep"][tier]), idx)
    spirit_mult = float(spirit["tierBase"][tier]) * pow(float(spirit["tierStep"][tier]), idx)

    hp = round((20 + (attrs["str"] * 1.5) + (attrs["con"] * 2.5)) * health_mult)
    spirit_points = round((15 + (attrs["wil"] * 2.2) + (attrs["int"] * 1.2) + (attrs["luck"] // 4)) * spirit_mult)
    return hp, spirit_points


def run_balance_calibration(cfg, balance_gate_mode, warnings):
    print(f"[phase2] running balance calibration (mode={balance_gate_mode})")
    if balance_gate_mode == "off":
        print("[phase2] balance calibration skipped by mode=off")
        return

    rows = load_core_tables()
    baseline_rows = [row for row in rows if row["table"] == "baseline_dpr_hp_spirit"]
    if len(baseline_rows) != 10:
        fail("baseline_dpr_hp_spirit table must contain exactly 10 rows")
    baseline_by_seq = {int(row["sequence"]): row for row in baseline_rows}

    attrs_by_seq = compute_progressed_attributes(cfg)
    tolerance_pct = 12.0
    findings = []
    deltas = []

    for seq in [int(v) for v in cfg["sequence"]["order"]]:
        attrs = attrs_by_seq[seq]
        hp_calc, spirit_calc = compute_derived_hp_spirit(cfg, seq, attrs)
        row = baseline_by_seq.get(seq)
        if row is None:
            fail(f"Missing baseline row for sequence {seq}")

        hp_mid = (float(row["hp_min"]) + float(row["hp_max"])) / 2.0
        spirit_mid = (float(row["spirit_min"]) + float(row["spirit_max"])) / 2.0

        hp_delta_pct = abs(hp_calc - hp_mid) / hp_mid * 100.0
        spirit_delta_pct = abs(spirit_calc - spirit_mid) / spirit_mid * 100.0
        deltas.append(
            {
                "sequence": seq,
                "hp_delta_pct": round(hp_delta_pct, 2),
                "spirit_delta_pct": round(spirit_delta_pct, 2),
            }
        )

        if hp_delta_pct > tolerance_pct:
            findings.append(
                f"sequence {seq} hp delta {hp_delta_pct:.2f}% exceeds tolerance {tolerance_pct:.2f}%"
            )
        if spirit_delta_pct > tolerance_pct:
            findings.append(
                f"sequence {seq} spirit delta {spirit_delta_pct:.2f}% exceeds tolerance {tolerance_pct:.2f}%"
            )

    print("[phase2] balance calibration deltas:", sorted(deltas, key=lambda d: d["sequence"], reverse=True))

    if findings:
        if balance_gate_mode == "strict":
            fail("Balance calibration failed under strict gate: " + "; ".join(findings))
        for finding in findings:
            warnings.append("[balance] " + finding)


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
    if "target" not in effect_obj:
        errors.append("missing_target")
    if "trigger" not in effect_obj:
        errors.append("missing_trigger")

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


def validate_item_semantics(item_obj, formula_keys, current_version, warnings):
    errors = []

    dependencies = item_obj.get("dependencies")
    if dependencies is None:
        errors.append("missing_dependencies")
    else:
        min_v = dependencies.get("minSystemVersion")
        max_v = dependencies.get("maxTestedSystemVersion")
        if min_v is None or max_v is None:
            errors.append("missing_dependency_semver_fields")
        else:
            try:
                ensure_semver_window(min_v, max_v, current_version, f"item:{item_obj.get('id','unknown')}", warnings)
            except AssertionError as exc:
                errors.append(str(exc))

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
        if "abilityData" not in item_obj:
            errors.append("missing_abilityData")

    if item_obj.get("type") == "weapon" and "weaponData" not in item_obj:
        errors.append("missing_weaponData")
    if item_obj.get("type") == "armor" and "armorData" not in item_obj:
        errors.append("missing_armorData")
    if item_obj.get("type") == "ritual" and "ritualData" not in item_obj:
        errors.append("missing_ritualData")
    if item_obj.get("type") == "artifact" and "artifactData" not in item_obj:
        errors.append("missing_artifactData")

    return errors


def validate_manifest(manifest, current_version, warnings):
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

    if ID_RE.fullmatch(manifest.get("packId", "")) is None:
        return False, "invalid_pack_id"

    try:
        parse_semver(manifest["packVersion"], "manifest.packVersion")
        ensure_semver_window(
            manifest["minSystemVersion"],
            manifest["maxTestedSystemVersion"],
            current_version,
            f"manifest:{manifest['packId']}",
            warnings,
        )
    except AssertionError as exc:
        return False, f"semver_error:{exc}"

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


def validate_manifest_dependency_graph(manifests):
    pack_ids = [manifest["packId"] for manifest in manifests]
    if len(pack_ids) != len(set(pack_ids)):
        return False, "duplicate_pack_ids"
    pack_id_set = set(pack_ids)

    graph = {}
    for manifest in manifests:
        deps = manifest.get("dependencies", [])
        for dep in deps:
            if dep not in pack_id_set:
                return False, f"missing_dependency:{dep}"
        graph[manifest["packId"]] = list(deps)

    visiting = set()
    visited = set()

    def dfs(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for nxt in graph[node]:
            if dfs(nxt):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    for node in graph:
        if dfs(node):
            return False, "dependency_cycle"
    return True, "ok"


def check_conditions_library(whitelist_prefixes, actor_track_props):
    library = load_json(ROOT / "data" / "conditions.library.v1.1.json")
    conditions = library.get("conditions", [])
    if not isinstance(conditions, list) or not conditions:
        fail("conditions.library.v1.1.json must contain non-empty conditions list")
    ids = [condition.get("id") for condition in conditions]
    if len(ids) != len(set(ids)):
        fail("conditions library contains duplicate condition IDs")
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
    missing_required = sorted(required_ids - got)
    if missing_required:
        fail(f"conditions library missing canonical IDs: {missing_required}")

    req_keys = {
        "id",
        "op",
        "sourceCategory",
        "target",
        "trigger",
        "applyPhase",
        "tickPhase",
        "durationRounds",
        "saveType",
        "saveTarget",
        "stackRule",
        "removeOn",
    }

    for condition in conditions:
        condition_id = condition.get("id")
        if not isinstance(condition_id, str) or ID_RE.fullmatch(condition_id) is None:
            fail(f"Invalid condition id format: {condition_id}")
        effects = condition.get("effects", [])
        if not effects:
            fail(f"Condition has no effects: {condition_id}")
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


def check_item_semantic_rules(cfg, current_version):
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
        "abilityData": {"targetMode": "enemy"},
        "dependencies": {
            "minSystemVersion": "1.1.0",
            "maxTestedSystemVersion": "1.1.0"
        }
    }
    if validate_item_semantics(valid_ability, formula_keys, current_version, []):
        fail("Valid ability failed semantic validation")

    bad_min_seq = dict(valid_ability)
    bad_min_seq["id"] = "ability.test.bad_seq"
    bad_min_seq["minSequence"] = 8
    errs = validate_item_semantics(bad_min_seq, formula_keys, current_version, [])
    if "ability_minSequence_gt_sequence" not in errs:
        fail("minSequence > sequence should fail semantic validation")

    bad_allowed = dict(valid_ability)
    bad_allowed["id"] = "ability.test.bad_allowed"
    bad_allowed["allowedPathwayIds"] = ["pathway.spectator"]
    errs = validate_item_semantics(bad_allowed, formula_keys, current_version, [])
    if "allowedPathwayIds_missing_pathwayId" not in errs:
        fail("allowedPathwayIds missing pathwayId should fail semantic validation")

    missing_deps = dict(valid_ability)
    missing_deps["id"] = "ability.test.missing_deps"
    missing_deps.pop("dependencies")
    errs = validate_item_semantics(missing_deps, formula_keys, current_version, [])
    if "missing_dependencies" not in errs:
        fail("missing dependencies should fail semantic validation")

    bad_formula = dict(valid_ability)
    bad_formula["id"] = "ability.test.bad_formula"
    bad_formula["formulaKey"] = "check.custom.future_formula"
    errs = validate_item_semantics(bad_formula, formula_keys, current_version, [])
    if "unknown_formula_key" not in errs:
        fail("Unknown formula key should fail semantic validation")

    missing_payload = dict(valid_ability)
    missing_payload["id"] = "ability.test.missing_payload"
    missing_payload.pop("abilityData")
    errs = validate_item_semantics(missing_payload, formula_keys, current_version, [])
    if "missing_abilityData" not in errs:
        fail("Missing abilityData should fail semantic validation")

    for item_type, payload_key in [
        ("weapon", "weaponData"),
        ("armor", "armorData"),
        ("ritual", "ritualData"),
        ("artifact", "artifactData"),
    ]:
        probe = {
            "id": f"{item_type}.test.missing_payload",
            "schemaVersion": 1,
            "name": f"{item_type} Missing Payload",
            "type": item_type,
            "dependencies": {"minSystemVersion": "1.1.0", "maxTestedSystemVersion": "1.1.0"},
        }
        if item_type == "ritual":
            probe["complexityClass"] = "invocation.standard_scope"
            probe["formulaKey"] = "check.ritual.v1"
            probe["effects"] = []
        if item_type == "artifact":
            probe["sourceSequence"] = 5
        errs = validate_item_semantics(probe, formula_keys, current_version, [])
        expected_error = f"missing_{payload_key}"
        if expected_error not in errs:
            fail(f"Missing {payload_key} should fail semantic validation")

    bad_semver_format = dict(valid_ability)
    bad_semver_format["id"] = "ability.test.bad_semver"
    bad_semver_format["dependencies"] = {"minSystemVersion": "1.1", "maxTestedSystemVersion": "1.1.0"}
    errs = validate_item_semantics(bad_semver_format, formula_keys, current_version, [])
    if not any("semver" in err for err in errs):
        fail("Invalid semver format should fail semantic validation")

    min_gt_max = dict(valid_ability)
    min_gt_max["id"] = "ability.test.min_gt_max"
    min_gt_max["dependencies"] = {"minSystemVersion": "1.2.0", "maxTestedSystemVersion": "1.1.0"}
    errs = validate_item_semantics(min_gt_max, formula_keys, current_version, [])
    if not any("minSystemVersion > maxTestedSystemVersion" in err for err in errs):
        fail("minSystemVersion > maxTestedSystemVersion should fail semantic validation")

    min_gt_current = dict(valid_ability)
    min_gt_current["id"] = "ability.test.min_gt_current"
    min_gt_current["dependencies"] = {"minSystemVersion": "9.0.0", "maxTestedSystemVersion": "9.0.0"}
    errs = validate_item_semantics(min_gt_current, formula_keys, current_version, [])
    if not any("requires newer system" in err for err in errs):
        fail("minSystemVersion > currentSystemVersion should fail semantic validation")

    warning_probe = []
    soft_warning = dict(valid_ability)
    soft_warning["id"] = "ability.test.soft_warning"
    soft_warning["dependencies"] = {"minSystemVersion": "1.0.0", "maxTestedSystemVersion": "1.0.0"}
    errs = validate_item_semantics(soft_warning, formula_keys, current_version, warning_probe)
    if errs:
        fail(f"Soft warning probe unexpectedly failed semantic validation: {errs}")
    if not warning_probe:
        fail("currentSystemVersion > maxTestedSystemVersion should emit soft warning")


def check_manifest_rules(current_version):
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
    ok, why = validate_manifest(valid_manifest, current_version, [])
    if not ok:
        fail(f"Valid manifest failed: {why}")

    invalid_schema = dict(valid_manifest)
    invalid_schema["schemaTarget"] = "v2"
    ok, why = validate_manifest(invalid_schema, current_version, [])
    if ok or why != "invalid_schema_target":
        fail("Invalid schema target test did not fail")

    invalid_empty = dict(valid_manifest)
    invalid_empty["entries"] = []
    ok, why = validate_manifest(invalid_empty, current_version, [])
    if ok or why != "entries_must_be_non_empty_list":
        fail("Empty entries test did not fail")

    invalid_dup_id = dict(valid_manifest)
    invalid_dup_id["entries"] = [
        {"id": "ability.seer.hunch_of_danger", "type": "ability", "path": "packs/a.json"},
        {"id": "ability.seer.hunch_of_danger", "type": "ability", "path": "packs/b.json"},
    ]
    ok, why = validate_manifest(invalid_dup_id, current_version, [])
    if ok or why != "duplicate_entry_ids":
        fail("Duplicate manifest ID test did not fail")

    invalid_dup_path = dict(valid_manifest)
    invalid_dup_path["entries"] = [
        {"id": "ability.seer.hunch_of_danger", "type": "ability", "path": "packs/shared.json"},
        {"id": "ability.seer.foresight", "type": "ability", "path": "packs/shared.json"},
    ]
    ok, why = validate_manifest(invalid_dup_path, current_version, [])
    if ok or why != "duplicate_entry_paths":
        fail("Duplicate manifest path test did not fail")

    invalid_unsafe_path = dict(valid_manifest)
    invalid_unsafe_path["entries"] = [
        {"id": "ability.seer.hunch_of_danger", "type": "ability", "path": "../secrets.json"}
    ]
    ok, why = validate_manifest(invalid_unsafe_path, current_version, [])
    if ok or why != "unsafe_entry_path":
        fail("Unsafe manifest path test did not fail")

    invalid_semver = dict(valid_manifest)
    invalid_semver["minSystemVersion"] = "1.1"
    ok, why = validate_manifest(invalid_semver, current_version, [])
    if ok or not why.startswith("semver_error:"):
        fail("Invalid manifest semver format test did not fail")

    min_gt_max = dict(valid_manifest)
    min_gt_max["minSystemVersion"] = "1.2.0"
    min_gt_max["maxTestedSystemVersion"] = "1.1.0"
    ok, why = validate_manifest(min_gt_max, current_version, [])
    if ok or "minSystemVersion > maxTestedSystemVersion" not in why:
        fail("Manifest minSystemVersion > maxTestedSystemVersion should fail")

    min_gt_current = dict(valid_manifest)
    min_gt_current["minSystemVersion"] = "9.0.0"
    min_gt_current["maxTestedSystemVersion"] = "9.0.0"
    ok, why = validate_manifest(min_gt_current, current_version, [])
    if ok or "requires newer system" not in why:
        fail("Manifest minSystemVersion > currentSystemVersion should fail")

    warning_probe = []
    soft_warning = dict(valid_manifest)
    soft_warning["minSystemVersion"] = "1.0.0"
    soft_warning["maxTestedSystemVersion"] = "1.0.0"
    ok, why = validate_manifest(soft_warning, current_version, warning_probe)
    if not ok:
        fail(f"Soft warning manifest probe unexpectedly failed: {why}")
    if not warning_probe:
        fail("Manifest currentSystemVersion > maxTestedSystemVersion should emit soft warning")

    graph_valid = [
        {
            "packId": "pack.a",
            "packVersion": "1.1.0",
            "schemaTarget": "v1.1",
            "minSystemVersion": "1.1.0",
            "maxTestedSystemVersion": "1.1.0",
            "entries": [{"id": "ability.a", "type": "ability", "path": "packs/a.json"}],
            "dependencies": [],
        },
        {
            "packId": "pack.b",
            "packVersion": "1.1.0",
            "schemaTarget": "v1.1",
            "minSystemVersion": "1.1.0",
            "maxTestedSystemVersion": "1.1.0",
            "entries": [{"id": "ability.b", "type": "ability", "path": "packs/b.json"}],
            "dependencies": ["pack.a"],
        },
    ]
    ok, why = validate_manifest_dependency_graph(graph_valid)
    if not ok:
        fail(f"Valid dependency graph failed: {why}")

    graph_missing = [dict(graph_valid[0]), dict(graph_valid[1])]
    graph_missing[1]["dependencies"] = ["pack.unknown"]
    ok, why = validate_manifest_dependency_graph(graph_missing)
    if ok or not why.startswith("missing_dependency:"):
        fail("Missing dependency graph test did not fail")

    graph_cycle = [dict(graph_valid[0]), dict(graph_valid[1])]
    graph_cycle[0]["dependencies"] = ["pack.b"]
    graph_cycle[1]["dependencies"] = ["pack.a"]
    ok, why = validate_manifest_dependency_graph(graph_cycle)
    if ok or why != "dependency_cycle":
        fail("Dependency cycle test did not fail")


def main():
    parser = argparse.ArgumentParser(description="Run Phase 2 verification checks.")
    parser.add_argument(
        "--balance-gate-mode",
        choices=sorted(BALANCE_GATE_MODES),
        help="Override balance gate mode (warn|strict|off). Defaults to config value.",
    )
    args = parser.parse_args()
    warnings = []

    print("[phase2] checking required files")
    ensure_required_files()

    print("[phase2] checking config contract")
    cfg, current_version, balance_mode = check_config_contract(args.balance_gate_mode)

    print("[phase2] checking schema identifiers and hardening contracts")
    check_schema_ids_and_contracts()

    print("[phase2] checking corruption boundary table")
    run_corruption_boundary_checks(cfg)

    print("[phase2] checking rolltable source contract")
    check_rolltable_source_contract()

    print("[phase2] checking skills registry")
    check_skill_registry()

    actor = load_json(ROOT / "schemas" / "actor.system.schema.v1_1.json")
    track_props = set(actor["properties"]["tracks"]["properties"].keys())

    print("[phase2] checking conditions library")
    check_conditions_library(cfg["validation"]["effectPathWhitelist"], track_props)

    print("[phase2] checking item semantic rules")
    check_item_semantic_rules(cfg, current_version)

    print("[phase2] checking manifest rules")
    check_manifest_rules(current_version)

    run_balance_calibration(cfg, balance_mode, warnings)

    if warnings:
        print("[phase2] soft warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print("ALL PHASE 2 CHECKS PASSED")


if __name__ == "__main__":
    main()
