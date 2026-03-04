import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PATH = ROOT / "system.json"

EXPECTED_ID = "lotm-system"
EXPECTED_REPO_URL = "https://github.com/brodybennett/FoundryVTTLoTMGameSystem"
EXPECTED_MANIFEST_URL = f"{EXPECTED_REPO_URL}/releases/latest/download/system.json"
EXPECTED_COMPAT_MIN = "13.347"
EXPECTED_COMPAT_VERIFIED = "13.347"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
PACK_PATH_RE = re.compile(r"^packs/[a-z0-9-]+\.db$")


REQUIRED_EXACT_PACKS = {
    "pathways",
    "abilities",
    "rituals",
    "sealed-artifacts",
    "items",
    "rolltables",
    "actors",
    "rules-reference",
}

ALLOWED_PACK_TYPES = {"Item", "RollTable", "Actor", "JournalEntry"}


def fail(msg: str) -> None:
    raise AssertionError(msg)


def ensure(condition: bool, msg: str) -> None:
    if not condition:
        fail(msg)


def verify_local_paths(manifest: dict) -> None:
    for path in manifest.get("esmodules", []):
        ensure((ROOT / path).exists(), f"Missing esmodule path: {path}")
    for path in manifest.get("styles", []):
        ensure((ROOT / path).exists(), f"Missing style path: {path}")
    for entry in manifest.get("languages", []):
        path = entry.get("path", "")
        ensure((ROOT / path).exists(), f"Missing language path: {path}")

    required = [
        "template.json",
        "README.md",
        "CHANGELOG.md",
        "LICENSE.md",
        "scripts/lotm-system.mjs",
        "module/constants.mjs",
        "module/actor/lotm-actor.mjs",
        "module/actor/validation.mjs",
        "module/item/lotm-item.mjs",
        "module/sheets/lotm-actor-sheet.mjs",
        "module/sheets/lotm-item-sheet.mjs",
        "module/rolls/roll-engine.mjs",
        "module/rolls/rolltable-engine.mjs",
        "module/chat/chat-cards.mjs",
        "module/migrations/v1_2_0.mjs",
        "templates/sheets/actor-sheet.hbs",
        "templates/sheets/item-sheet.hbs",
        "templates/chat/check-card.hbs",
        "templates/chat/info-card.hbs",
        "content-src",
        "data",
        "schemas",
        "schemas/content.rolltable.schema.v1_2.json",
        "system-config-v1.1.json",
        "packs",
    ]
    for rel in required:
        ensure((ROOT / rel).exists(), f"Missing required package asset: {rel}")


def verify_packs(manifest: dict) -> None:
    packs = manifest.get("packs", [])
    ensure(isinstance(packs, list) and packs, "system.packs must be a non-empty array")

    names = []
    seen = set()
    for pack in packs:
        for key in ["name", "label", "type", "path"]:
            ensure(key in pack, f"Pack entry missing key: {key}")

        name = pack["name"]
        ensure(name not in seen, f"Duplicate pack name: {name}")
        seen.add(name)
        names.append(name)

        ensure(pack["type"] in ALLOWED_PACK_TYPES, f"Pack {name} has unsupported type {pack['type']}")
        ensure(PACK_PATH_RE.fullmatch(pack["path"]) is not None, f"Pack {name} has invalid path {pack['path']}")
        ensure((ROOT / pack["path"]).exists(), f"Pack file does not exist: {pack['path']}")

    missing_exact = sorted(REQUIRED_EXACT_PACKS - set(names))
    ensure(not missing_exact, f"Missing required packs in manifest: {missing_exact}")


def main() -> None:
    ensure(SYSTEM_PATH.exists(), "system.json not found at repository root")
    manifest = json.loads(SYSTEM_PATH.read_text(encoding="utf-8"))

    required_keys = [
        "id",
        "title",
        "description",
        "version",
        "authors",
        "compatibility",
        "esmodules",
        "styles",
        "languages",
        "url",
        "manifest",
        "download",
        "packs",
        "license",
        "readme",
        "changelog",
    ]
    for key in required_keys:
        ensure(key in manifest, f"Missing required key in system.json: {key}")

    ensure(manifest["id"] == EXPECTED_ID, f"system.id must be {EXPECTED_ID}")
    ensure(SEMVER_RE.fullmatch(manifest["version"]) is not None, "system.version must be semver X.Y.Z")
    ensure(manifest["url"] == EXPECTED_REPO_URL, "system.url mismatch")
    ensure(manifest["manifest"] == EXPECTED_MANIFEST_URL, "system.manifest mismatch")

    expected_download = (
        f"{EXPECTED_REPO_URL}/releases/download/v{manifest['version']}/"
        f"{EXPECTED_ID}-v{manifest['version']}.zip"
    )
    ensure(manifest["download"] == expected_download, "system.download must match v<version>/lotm-system-v<version>.zip")

    compatibility = manifest.get("compatibility", {})
    ensure(compatibility.get("minimum") == EXPECTED_COMPAT_MIN, "compatibility.minimum mismatch")
    ensure(compatibility.get("verified") == EXPECTED_COMPAT_VERIFIED, "compatibility.verified mismatch")

    authors = manifest.get("authors", [])
    ensure(isinstance(authors, list) and len(authors) >= 1, "authors must be a non-empty array")
    for author in authors:
        ensure("name" in author and str(author["name"]).strip(), "each author must include name")

    verify_local_paths(manifest)
    verify_packs(manifest)
    print("[foundry-manifest] PASS")


if __name__ == "__main__":
    main()
