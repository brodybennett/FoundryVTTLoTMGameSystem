import argparse
import json
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]


def migrate_actor_system(actor_system: dict) -> tuple[dict, dict]:
    migrated = json.loads(json.dumps(actor_system))
    report = {
        "added_fields": 0,
        "defaulted_paths": [],
    }

    if "tracks" not in migrated:
        migrated["tracks"] = {}
        report["added_fields"] += 1
        report["defaulted_paths"].append("tracks")
    tracks = migrated["tracks"]

    if "threatClocks" not in tracks:
        tracks["threatClocks"] = []
        report["added_fields"] += 1
        report["defaulted_paths"].append("tracks.threatClocks")
    if "influence" not in tracks:
        tracks["influence"] = {}
        report["added_fields"] += 1
        report["defaulted_paths"].append("tracks.influence")
    if "leverage" not in tracks:
        tracks["leverage"] = {}
        report["added_fields"] += 1
        report["defaulted_paths"].append("tracks.leverage")

    if "ritual" not in migrated:
        migrated["ritual"] = {}
        report["added_fields"] += 1
        report["defaulted_paths"].append("ritual")
    if "instability" not in migrated["ritual"]:
        migrated["ritual"]["instability"] = 0
        report["added_fields"] += 1
        report["defaulted_paths"].append("ritual.instability")

    if "artifacts" not in migrated:
        migrated["artifacts"] = {}
        report["added_fields"] += 1
        report["defaulted_paths"].append("artifacts")
    if "sceneUsesById" not in migrated["artifacts"]:
        migrated["artifacts"]["sceneUsesById"] = {}
        report["added_fields"] += 1
        report["defaulted_paths"].append("artifacts.sceneUsesById")

    return migrated, report


def run_idempotence_check(actor_system: dict):
    once, report_once = migrate_actor_system(actor_system)
    twice, report_twice = migrate_actor_system(once)
    if once != twice:
        raise AssertionError("Migration is not idempotent.")
    return once, report_once, report_twice


def load_input(path: Optional[Path]):
    if path is None:
        return {
            "identity": {"pathwayId": "pathway.seer", "sequence": 9, "tier": "low"},
            "attributes": {k: {"base": 10, "temp": 0} for k in ["str", "dex", "wil", "con", "cha", "int", "luck"]},
            "skills": {"ritualism": {"linkedAttr": "wil", "rank": "trained", "misc": 0}},
            "derived": {"hpMax": 60, "spiritMax": 55, "sanityMax": 64, "defenseShift": 0, "initiativeTarget": 30},
            "resources": {"hp": 60, "spirit": 55, "corruption": 0, "deathMarks": 0},
            "progression": {"gates": {"narrative": False, "economy": False, "stability": True}},
            "version": {"schemaVersion": 1},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Idempotent v1 -> v1.1 migration helper.")
    parser.add_argument("--input", help="Path to actor.system json payload")
    parser.add_argument("--output", help="Output path for migrated payload")
    parser.add_argument("--dry-run", action="store_true", help="Run migration checks without writing output")
    args = parser.parse_args()

    in_path = Path(args.input) if args.input else None
    out_path = Path(args.output) if args.output else None

    source = load_input(in_path)
    migrated, report_once, report_twice = run_idempotence_check(source)

    report = {
        "mode": "dry-run" if args.dry_run else "apply",
        "source": str(in_path) if in_path else "embedded-sample",
        "idempotent": True,
        "first_pass": report_once,
        "second_pass": report_twice,
    }

    if args.dry_run:
        print(json.dumps(report, indent=2))
        print("MIGRATION DRY-RUN PASS")
        return

    if out_path:
        out_path.write_text(json.dumps(migrated, indent=2), encoding="utf-8")
        print(f"Wrote migrated payload: {out_path}")
    else:
        print(json.dumps(migrated, indent=2))

    report_path = ROOT / "migration-report-v1-to-v1.1.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote migration report: {report_path}")
    print("MIGRATION APPLY PASS")


if __name__ == "__main__":
    main()
