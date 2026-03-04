import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PATH = ROOT / "system.json"
CONSTANTS_PATH = ROOT / "module" / "constants.mjs"
CONFIG_PATH = ROOT / "system-config-v1.1.json"
TEMPLATE_PATH = ROOT / "template.json"
CONTENT_TOOL_PATH = ROOT / "scripts" / "content_tool.py"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def fail(msg: str) -> None:
    raise AssertionError(msg)


def ensure(condition: bool, msg: str) -> None:
    if not condition:
        fail(msg)


def read_json(path: Path) -> dict:
    ensure(path.exists(), f"Missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_system_version() -> str:
    payload = read_json(SYSTEM_PATH)
    version = payload.get("version")
    ensure(isinstance(version, str), "system.json version must be a string")
    ensure(SEMVER_RE.fullmatch(version) is not None, "system.json version must be semver X.Y.Z")
    return version


def extract_world_schema_version() -> str:
    ensure(CONSTANTS_PATH.exists(), "module/constants.mjs is missing")
    content = CONSTANTS_PATH.read_text(encoding="utf-8")
    match = re.search(r'WORLD_SCHEMA_VERSION\s*=\s*"([^"]+)"', content)
    ensure(match is not None, "WORLD_SCHEMA_VERSION constant was not found in module/constants.mjs")
    version = match.group(1)
    ensure(SEMVER_RE.fullmatch(version) is not None, "WORLD_SCHEMA_VERSION must be semver X.Y.Z")
    return version


def verify_content_tool() -> None:
    ensure(CONTENT_TOOL_PATH.exists(), "scripts/content_tool.py is missing")
    content = CONTENT_TOOL_PATH.read_text(encoding="utf-8")
    ensure("def get_system_version" in content, "content_tool.py must define get_system_version()")
    ensure('ROOT / "system.json"' in content, "content_tool.py must read version from system.json")
    ensure("SYSTEM_VERSION" not in content, "content_tool.py must not define a hardcoded SYSTEM_VERSION constant")


def main() -> None:
    system_version = load_system_version()
    world_schema_version = extract_world_schema_version()
    config_payload = read_json(CONFIG_PATH)
    template_payload = read_json(TEMPLATE_PATH)

    config_version = config_payload.get("configVersion")
    ensure(isinstance(config_version, str), "system-config-v1.1.json configVersion must be a string")
    ensure(SEMVER_RE.fullmatch(config_version) is not None, "configVersion must be semver X.Y.Z")

    template_deps = template_payload.get("Item", {}).get("templates", {}).get("base", {}).get("dependencies", {})
    template_max_tested = template_deps.get("maxTestedSystemVersion")
    ensure(
        isinstance(template_max_tested, str),
        "template.json Item.templates.base.dependencies.maxTestedSystemVersion must be a string",
    )
    ensure(
        SEMVER_RE.fullmatch(template_max_tested) is not None,
        "template maxTestedSystemVersion must be semver X.Y.Z",
    )

    verify_content_tool()

    ensure(
        world_schema_version == system_version,
        f"WORLD_SCHEMA_VERSION ({world_schema_version}) must match system.json version ({system_version})",
    )
    ensure(
        config_version == system_version,
        f"configVersion ({config_version}) must match system.json version ({system_version})",
    )
    ensure(
        template_max_tested == system_version,
        (
            "template.json Item.templates.base.dependencies.maxTestedSystemVersion "
            f"({template_max_tested}) must match system.json version ({system_version})"
        ),
    )

    print("[version-consistency] PASS")


if __name__ == "__main__":
    main()
