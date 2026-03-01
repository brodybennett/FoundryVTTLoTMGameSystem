import csv
import json
import random
import subprocess
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(msg: str) -> None:
    raise AssertionError(msg)


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def resolve_advancement(rolls, targets):
    stages = ["preparation", "channeling", "integration"]
    if set(rolls.keys()) != set(stages) or set(targets.keys()) != set(stages):
        fail("Advancement resolver input must include all 3 stages.")
    passes = 0
    backlash = False
    detail = {}
    for stage in stages:
        roll = int(rolls[stage])
        target = clamp(int(targets[stage]), 1, 95)
        if roll == 1:
            success = True
            margin = abs(target - roll) + 10
        elif roll == 100:
            success = False
            margin = abs(target - roll)
            backlash = True
        else:
            success = roll <= target
            margin = abs(target - roll)
        if success:
            passes += 1
        detail[stage] = {"roll": roll, "target": target, "success": success, "margin": margin}
    outcome = "success" if passes >= 2 else ("failed" if passes == 1 else "severe_failed")
    return {"passes": passes, "backlash": backlash, "outcome": outcome, "detail": detail}


def corruption_penalty(pct: float, bands=None) -> int:
    table = bands or [
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
    value = float(pct)
    for band in table:
        if float(band["startPct"]) <= value <= float(band["endPct"]):
            return int(band["penalty"])
    fail(f"No corruption penalty band matched pct={pct}.")


def resolve_death_check(roll: int, target: int, marks: int, saves: int):
    target = clamp(int(target), 1, 95)
    roll = int(roll)
    marks = int(marks)
    saves = int(saves)

    if roll == 1:
        saves += 2
    elif roll == 100:
        marks += 2
    elif roll <= target:
        saves += 1
    else:
        marks += 1

    marks = min(3, marks)
    saves = min(3, saves)
    state = "dead" if marks >= 3 else ("stabilized" if saves >= 3 else "ongoing")
    return {"roll": roll, "target": target, "marks": marks, "saves": saves, "state": state}


def load_core_tables():
    rows = []
    with (ROOT / "core-tables-v1.csv").open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows


def run_unit_checks(config):
    print("[unit] checking formula/config consistency")
    if config["checks"]["targetClamp"]["max"] != 95:
        fail("Target clamp max must be 95.")
    if abs(config["recovery"]["shortRestMultiplier"] - 0.45) > 1e-9:
        fail("Short rest multiplier must be 0.45.")
    if config["corruption"]["penaltyPerBand"] != -1:
        fail("Corruption penalty per band must be -1.")
    if config["corruption"]["maxUniversalPenalty"] != -10:
        fail("Corruption max penalty cap must be -10.")
    bands = config["corruption"].get("penaltyBands", [])
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
    if bands != expected_bands:
        fail("Corruption penalty bands must match canonical Phase 2 band table.")
    scale = config["corruption"].get("trackScale", {})
    if scale.get("min") != 0 or scale.get("max") != 100 or scale.get("unit") != "points":
        fail("Corruption track scale must be explicit 0..100 points.")

    if config["combat"]["actionEconomy"]["universalBonusAction"]:
        fail("Universal bonus action must remain disabled.")
    attack_formula = config.get("formulaRegistry", {}).get("check.attack.v1", "")
    if "attackAttribute/3" not in attack_formula:
        fail("check.attack.v1 must include attackAttribute/3 scaling.")
    damage_formula = config.get("formulaRegistry", {}).get("calc.damage.final.v1", "")
    if "max(1" not in damage_formula:
        fail("calc.damage.final.v1 must enforce minimum hit damage of 1.")

    ritual_formula = config.get("formulaRegistry", {}).get("check.ritual.v1", "")
    if "/9" not in ritual_formula or "/3" in ritual_formula:
        fail("check.ritual.v1 must use attribute divisor /9 and not /3.")

    adv = config.get("advancement", {})
    if adv.get("checksByStage", {}).get("channeling") != "willpower":
        fail("Advancement channeling default check must be willpower.")
    channeling = adv.get("channelingSelection", {})
    if channeling.get("alternateSkill") != "endurance" or channeling.get("declareBeforeRoll") is not True:
        fail("Advancement channeling selection contract is invalid.")
    one_pass = adv.get("failureConsequences", {}).get("onePass", {})
    zero_pass = adv.get("failureConsequences", {}).get("zeroPass", {})
    backlash = adv.get("failureConsequences", {}).get("criticalBacklash", {})
    if one_pass.get("corruptionGainFlat") != 8:
        fail("One-pass advancement failure must apply +8 flat corruption.")
    if zero_pass.get("corruptionGainFlat") != 15:
        fail("Zero-pass advancement failure must apply +15 flat corruption.")
    if backlash.get("corruptionGainFlat") != 25:
        fail("Critical backlash must apply +25 flat corruption.")
    if any("corruptionGainPctOfMaxSanity" in bucket for bucket in [one_pass, zero_pass, backlash]):
        fail("Percent-of-max-sanity corruption penalties are no longer allowed.")

    death_track = config.get("combat", {}).get("deathTrack", {})
    if death_track.get("maxMarks") != 3 or death_track.get("maxSaves") != 3:
        fail("Death track must be configured to 3 marks and 3 saves.")
    if death_track.get("damageWhileDownedAddsMarks") != 1:
        fail("Damage while downed must add exactly 1 death mark.")

    boundary_expectations = {0: 0, 9: 0, 10: -1, 59: -5, 60: -6, 69: -6, 70: -7, 89: -8, 90: -10, 100: -10}
    for pct, expected in boundary_expectations.items():
        got = corruption_penalty(pct, bands)
        if got != expected:
            fail(f"Corruption penalty mismatch at {pct}%: got {got}, expected {expected}.")

    sample_rolls = {"preparation": 1, "channeling": 67, "integration": 100}
    sample_targets = {"preparation": 62, "channeling": 70, "integration": 66}
    a = resolve_advancement(sample_rolls, sample_targets)
    b = resolve_advancement(sample_rolls, sample_targets)
    if a != b:
        fail("Advancement resolver is non-deterministic for identical inputs.")
    if a["detail"]["preparation"]["margin"] != abs(62 - 1) + 10:
        fail("Natural 1 margin bonus rule failed.")
    if not a["backlash"]:
        fail("Natural 100 must trigger backlash flag.")

    if resolve_death_check(1, 50, 0, 0) != {"roll": 1, "target": 50, "marks": 0, "saves": 2, "state": "ongoing"}:
        fail("Death resolver natural 1 behavior failed.")
    if resolve_death_check(100, 50, 0, 0) != {"roll": 100, "target": 50, "marks": 2, "saves": 0, "state": "ongoing"}:
        fail("Death resolver natural 100 behavior failed.")
    if resolve_death_check(88, 60, 2, 0)["state"] != "dead":
        fail("Death resolver death threshold behavior failed.")
    if resolve_death_check(40, 50, 0, 2)["state"] != "stabilized":
        fail("Death resolver stabilization behavior failed.")


def run_combat_simulation(rows):
    print("[sim] running parity combat simulation")
    baseline = [r for r in rows if r["table"] == "baseline_dpr_hp_spirit"]
    if len(baseline) != 10:
        fail("Baseline DPR/HP/Spirit table must contain 10 rows.")

    medians = {}
    trials = 10000
    for row in baseline:
        seq = int(row["sequence"])
        hp_min = float(row["hp_min"])
        hp_max = float(row["hp_max"])
        dpr_min = float(row["dpr_min"])
        dpr_max = float(row["dpr_max"])
        rounds = []
        for _ in range(trials):
            hp_a = random.uniform(hp_min, hp_max)
            hp_b = random.uniform(hp_min, hp_max)
            round_count = 0
            while hp_a > 0 and hp_b > 0 and round_count < 60:
                round_count += 1
                dmg_a = max(1.0, random.uniform(dpr_min, dpr_max) * random.uniform(0.8, 1.2))
                dmg_b = max(1.0, random.uniform(dpr_min, dpr_max) * random.uniform(0.8, 1.2))
                hp_b -= dmg_a
                hp_a -= dmg_b
            rounds.append(round_count)
        med = statistics.median(rounds)
        medians[seq] = med
        if not (6 <= med <= 9):
            fail(f"Sequence {seq} parity median rounds out of range: {med}")
    print("[sim] combat medians:", dict(sorted(medians.items(), reverse=True)))


def run_ritual_simulation():
    print("[sim] running ritual success simulation")
    bands = {
        "mid": (65, 75, 70),
        "high": (55, 65, 60),
        "demigod": (45, 55, 50),
        "angel": (35, 45, 40),
        "god": (25, 35, 30),
    }
    trials = 10000
    observed = {}
    for tier, (lo, hi, target) in bands.items():
        wins = 0
        for _ in range(trials):
            roll = random.randint(1, 100)
            if roll <= target:
                wins += 1
        rate = (wins / trials) * 100
        observed[tier] = round(rate, 2)
        if not (lo <= rate <= hi):
            fail(f"Ritual success rate for {tier} out of band: {rate:.2f}%")
    print("[sim] ritual rates:", observed)


def run_corruption_campaign_sim():
    print("[sim] running corruption campaign simulation")
    campaigns = 5000
    terminal = 0
    finals = []
    for _ in range(campaigns):
        corruption = 0.0
        done = False
        for _session in range(20):
            risky_uses = 1 + (1 if random.random() < 0.4 else 0)
            for _ in range(risky_uses):
                gain = random.randint(3, 8)
                resistance = random.randint(0, 3)
                net = max(1, gain - resistance)
                corruption += net
            # Rare high-risk spike from ritual backlash/artifact misuse.
            if random.random() < 0.08:
                corruption += random.randint(12, 28)
            recovery = random.randint(3, 6)
            corruption = max(0.0, corruption - recovery)
            if corruption >= 100:
                terminal += 1
                done = True
                break
        finals.append(100.0 if done else corruption)
    median_final = statistics.median(finals)
    terminal_rate = (terminal / campaigns) * 100
    if not (20 <= median_final <= 70):
        fail(f"Campaign corruption pressure failed median range: {median_final:.2f}")
    if not (0 < terminal_rate < 10):
        fail(f"Terminal corruption rate out of bounds: {terminal_rate:.2f}%")
    print(f"[sim] corruption median={median_final:.2f}, terminal_rate={terminal_rate:.2f}%")


def validate_item(item, known_ids, formula_keys):
    errors = []
    allowed_types = {
        "pathway",
        "sequenceNode",
        "ability",
        "ritual",
        "artifact",
        "weapon",
        "armor",
        "consumable",
        "ingredient",
        "background",
        "conditionTemplate",
    }
    if item.get("type") not in allowed_types:
        errors.append("invalid_type")

    if item.get("type") == "ability":
        required = ["pathwayId", "sequence", "minSequence", "activation", "resource", "cost", "cooldown", "formulaKey", "effects", "abilityData"]
        for field in required:
            if field not in item:
                errors.append(f"missing_{field}")
        if "formulaKey" in item and item["formulaKey"] not in formula_keys:
            errors.append("invalid_formula_key")

    deps = item.get("dependencies", {})
    for dep_id in deps.get("requiresIds", []):
        if dep_id not in known_ids:
            errors.append("missing_dependency")
            break
    return errors


def run_content_validation_checks(config):
    print("[content] running validation rule checks")
    formula_keys = set(config["formulaRegistry"].keys())
    known_ids = {"pathway.seer", "condition.stunned", "ability.seer.hunch_of_danger"}

    invalid_enum = {"id": "test.invalid", "schemaVersion": 1, "name": "Invalid", "type": "badtype"}
    if not validate_item(invalid_enum, known_ids, formula_keys):
        fail("Invalid enum test did not fail.")

    missing_formula = {
        "id": "ability.test.no_formula",
        "schemaVersion": 1,
        "name": "No Formula",
        "type": "ability",
        "pathwayId": "pathway.seer",
        "sequence": 9,
        "minSequence": 9,
        "activation": "action",
        "resource": "spirit",
        "cost": 5,
        "cooldown": 1,
        "effects": [],
        "abilityData": {"targetMode": "enemy"}
    }
    errs = validate_item(missing_formula, known_ids, formula_keys)
    if "missing_formulaKey" not in errs:
        fail("Missing formulaKey test did not fail.")

    missing_dep = {
        "id": "ability.test.dep",
        "schemaVersion": 1,
        "name": "Missing Dep",
        "type": "ability",
        "pathwayId": "pathway.seer",
        "sequence": 9,
        "minSequence": 9,
        "activation": "action",
        "resource": "spirit",
        "cost": 5,
        "cooldown": 1,
        "formulaKey": "check.skill.v1",
        "effects": [],
        "abilityData": {"targetMode": "enemy"},
        "dependencies": {"requiresIds": ["pathway.unknown"]}
    }
    errs = validate_item(missing_dep, known_ids, formula_keys)
    if "missing_dependency" not in errs:
        fail("Missing dependency test did not fail.")

    v1_actor = {
        "identity": {"pathwayId": "pathway.seer", "sequence": 9, "tier": "low"},
        "attributes": {k: {"base": 10, "temp": 0} for k in ["str", "dex", "wil", "con", "cha", "int", "luck"]},
        "skills": {"ritualism": {"linkedAttr": "wil", "rank": "trained", "misc": 0}},
        "derived": {"hpMax": 60, "spiritMax": 55, "sanityMax": 64, "defenseShift": 0, "initiativeTarget": 30},
        "resources": {"hp": 60, "spirit": 55, "corruption": 0, "deathMarks": 0},
        "progression": {"gates": {"narrative": False, "economy": False, "stability": True}},
        "version": {"schemaVersion": 1}
    }

    def migrate_v1_to_v1p1(actor):
        migrated = json.loads(json.dumps(actor))
        migrated.setdefault("tracks", {})
        migrated["tracks"].setdefault("investigationIP", 0)
        migrated.setdefault("resources", {})
        migrated["resources"].setdefault("deathSaves", 0)
        migrated.setdefault("combat", {})
        migrated["combat"].setdefault("armor", 0)
        migrated["combat"].setdefault("cover", 0)
        migrated["combat"].setdefault("encumbrancePenalty", 0)
        migrated["combat"].setdefault("damageReduction", 0)
        migrated["combat"].setdefault("actionBudget", {"actions": 1, "moves": 1, "reactions": 1, "bonusActions": 0})
        return migrated

    migrated = migrate_v1_to_v1p1(v1_actor)
    if migrated["identity"]["pathwayId"] != v1_actor["identity"]["pathwayId"]:
        fail("Migration compatibility test failed to preserve required field.")
    if migrated["resources"]["deathSaves"] != 0:
        fail("Migration compatibility test failed to seed deathSaves.")
    if migrated["combat"]["actionBudget"]["actions"] != 1:
        fail("Migration compatibility test failed to seed combat action budget.")


def run_rulebook_contract_audit():
    print("[contract] running rulebook contract audit")
    script = ROOT / "scripts" / "rulebook_contract_audit.py"
    rulebook = ROOT / "rulebook-source-v1.1.md"
    if not script.exists():
        fail(f"Missing contract audit script: {script}")
    if not rulebook.exists():
        fail(f"Missing rulebook source for audit: {rulebook}")
    cmd = [sys.executable, str(script), "--rulebook", str(rulebook)]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        msg = proc.stdout + "\n" + proc.stderr
        fail(f"Rulebook contract audit failed.\n{msg.strip()}")


def main():
    required = [
        ROOT / "rules-canon-v1.1.md",
        ROOT / "rulebook-source-v1.1.md",
        ROOT / "system-config-v1.1.json",
        ROOT / "foundry-schema-v1.1.md",
        ROOT / "core-tables-v1.csv",
        ROOT / "content-validation-rules-v1.1.md",
        ROOT / "phase1-test-matrix-v1.1.md",
        ROOT / "decision-log-v1.1.md",
        ROOT / "schemas" / "actor.system.schema.v1_1.json",
        ROOT / "schemas" / "item.system.schema.v1_1.json",
        ROOT / "schemas" / "effect.schema.v1_1.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        fail(f"Missing required artifact files: {missing}")

    config = json.loads((ROOT / "system-config-v1.1.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "schemas" / "actor.system.schema.v1_1.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "schemas" / "item.system.schema.v1_1.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "schemas" / "effect.schema.v1_1.json").read_text(encoding="utf-8"))

    rows = load_core_tables()
    tables = {r["table"] for r in rows}
    expected_tables = {
        "attribute_modifier",
        "corruption_threshold",
        "ritual_complexity",
        "sequence_advancement",
        "baseline_dpr_hp_spirit",
    }
    if not expected_tables.issubset(tables):
        fail(f"Core tables missing expected table groups. Found={tables}")

    run_unit_checks(config)
    run_combat_simulation(rows)
    run_ritual_simulation()
    run_corruption_campaign_sim()
    run_content_validation_checks(config)
    run_rulebook_contract_audit()
    print("ALL PHASE 1 CHECKS PASSED")


if __name__ == "__main__":
    random.seed(1337)
    main()
