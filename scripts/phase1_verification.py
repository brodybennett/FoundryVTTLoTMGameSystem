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


def corruption_penalty(pct: float) -> int:
    return max(-6, -1 * int(pct // 10))


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
    if config["corruption"]["maxUniversalPenalty"] != -6:
        fail("Corruption max penalty cap must be -6.")

    boundary_expectations = {
        0: 0,
        9: 0,
        10: -1,
        59: -5,
        60: -6,
        99: -6,
        100: -6,
    }
    for pct, expected in boundary_expectations.items():
        got = corruption_penalty(pct)
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
        required = ["pathwayId", "sequence", "minSequence", "activation", "resource", "cost", "cooldown", "formulaKey", "effects"]
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
        "effects": []
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
        return migrated

    migrated = migrate_v1_to_v1p1(v1_actor)
    if migrated["identity"]["pathwayId"] != v1_actor["identity"]["pathwayId"]:
        fail("Migration compatibility test failed to preserve required field.")


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
