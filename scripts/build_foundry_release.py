import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PATH = ROOT / "system.json"
DIST_DIR = ROOT / "dist"

REQUIRED_KEYS = [
    "id",
    "version",
    "manifest",
    "download",
    "compatibility",
    "esmodules",
    "styles",
    "languages",
    "packs",
]


def fail(msg: str) -> None:
    raise AssertionError(msg)


def ensure(condition: bool, msg: str) -> None:
    if not condition:
        fail(msg)


def run_step(label: str, command: list[str]) -> None:
    print(f"[foundry-build] {label}")
    proc = subprocess.run(command, cwd=str(ROOT))
    if proc.returncode != 0:
        fail(f"{label} failed with exit code {proc.returncode}")


def load_manifest() -> dict:
    ensure(SYSTEM_PATH.exists(), "system.json not found")
    manifest = json.loads(SYSTEM_PATH.read_text(encoding="utf-8"))
    for key in REQUIRED_KEYS:
        ensure(key in manifest, f"Missing required system.json key: {key}")
    ensure(isinstance(manifest["id"], str) and manifest["id"].strip(), "system.id must be non-empty string")
    ensure(isinstance(manifest["version"], str) and manifest["version"].strip(), "system.version must be non-empty string")
    return manifest


def copy_required_payload(stage_dir: Path) -> None:
    payload = [
        "system.json",
        "template.json",
        "README.md",
        "CHANGELOG.md",
        "LICENSE.md",
        "scripts",
        "module",
        "lang",
        "styles",
        "templates",
        "data",
        "schemas",
        "packs",
        "content-src",
        "docs",
        "system-config-v1.1.json",
    ]
    for rel in payload:
        src = ROOT / rel
        dst = stage_dir / rel
        ensure(src.exists(), f"Missing required package source path: {rel}")
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def build_zip(stage_root: Path, system_id: str, version: str) -> Path:
    zip_path = DIST_DIR / f"{system_id}-v{version}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(stage_root.rglob("*")):
            if file_path.is_file():
                relative = file_path.relative_to(stage_root)
                arcname = Path(system_id) / relative
                zf.write(file_path, arcname.as_posix())
    return zip_path


def main() -> None:
    run_step("Validate content source", [sys.executable, "scripts/validate_content_source.py"])
    run_step("Build compendium packs", [sys.executable, "scripts/build_compendiums.py"])

    manifest = load_manifest()
    system_id = manifest["id"]
    version = manifest["version"]

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    stage_dir = DIST_DIR / system_id
    stage_dir.mkdir(parents=True, exist_ok=True)

    copy_required_payload(stage_dir)
    zip_path = build_zip(stage_dir, system_id, version)

    release_manifest_path = DIST_DIR / "system.json"
    shutil.copy2(ROOT / "system.json", release_manifest_path)

    print(f"[foundry-build] staged: {stage_dir}")
    print(f"[foundry-build] zip: {zip_path}")
    print(f"[foundry-build] manifest asset: {release_manifest_path}")


if __name__ == "__main__":
    main()