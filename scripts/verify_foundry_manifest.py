import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PATH = ROOT / "system.json"

EXPECTED_ID = "lotm-system"
EXPECTED_VERSION = "1.1.0"
EXPECTED_REPO_URL = "https://github.com/brodybennett/FoundryVTTLoTMGameSystem"
EXPECTED_MANIFEST_URL = f"{EXPECTED_REPO_URL}/releases/latest/download/system.json"
EXPECTED_COMPAT_MIN = "13.347"
EXPECTED_COMPAT_VERIFIED = "13.347"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


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
        "templates/placeholder.html",
        "data",
        "schemas",
        "system-config-v1.1.json",
    ]
    for rel in required:
        ensure((ROOT / rel).exists(), f"Missing required package asset: {rel}")


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
        "license",
        "readme",
        "changelog",
    ]
    for key in required_keys:
        ensure(key in manifest, f"Missing required key in system.json: {key}")

    ensure(manifest["id"] == EXPECTED_ID, f"system.id must be {EXPECTED_ID}")
    ensure(manifest["version"] == EXPECTED_VERSION, f"system.version must be {EXPECTED_VERSION} for first release")
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
    print("[foundry-manifest] PASS")


if __name__ == "__main__":
    main()
