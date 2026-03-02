# Content Validation Rules v1.1

v1.1 extends v1 validation with registry and manifest checks.

## 1) Required Metadata

Every content entry must include:
- `id`
- `schemaVersion`
- `name`
- `type`
- `dependencies.minSystemVersion`
- `dependencies.maxTestedSystemVersion`

## 2) Required Registry Checks

- Registries are open-extension:
  - canonical required IDs must exist
  - additional IDs are allowed when they pass schema and uniqueness checks
- Skill-linked entries must use IDs present in `data/skills.registry.v1.1.json`.
- Condition templates must map to `data/conditions.library.v1.1.json` IDs.

## 3) Required Formula Checks

- `formulaKey` must exist in configured formula registry.
- Unknown formula keys are hard errors.
- `formulaKey` is not enum-locked at schema level; validator is authoritative for allowed keys.

## 4) Effect Path Safety

- Effect `path` must start with a whitelisted prefix from:
  `system-config-v1.1.json.validation.effectPathWhitelist`.

## 5) Effect Semantic Safety

- `sourceCategory` is required for runtime stacking and source-based conflict resolution.
- `target` is required for deterministic application scope.
- `trigger` is required for deterministic activation timing.
- If `saveType = none`, `saveTarget` must equal `0` and `removeOn` must not include `saveSuccess`.
- If `saveType != none`, `saveTarget` must be in `1..95`.
- If `op = cost`, `value` must be non-negative.

## 6) Item Semantic Checks

- Every item must include `dependencies.minSystemVersion` and `dependencies.maxTestedSystemVersion`.
- For `type = ability`, `minSequence <= sequence`.
- If both `pathwayId` and `allowedPathwayIds` are present, `allowedPathwayIds` must include `pathwayId`.
- `type = ability` requires `abilityData`.
- `type = weapon` requires `weaponData`.
- `type = armor` requires `armorData`.
- `type = ritual` requires `ritualData`.
- `type = artifact` requires `artifactData`.

## 7) Additive Item Field Checks

When present:
- `usageLimit.scope` must be one of default scopes.
- `usageLimit.maxUses` must be positive.
- `sourceSequence` must be `0..9`.
- `activation = bonusAction` is valid only for entries that explicitly mutate `system.combat.actionBudget.bonusActions`.

## 8) Manifest Checks (Required for Publish)

Manifest must pass:
- schema validation against `schemas/content.pack.manifest.schema.v1_1.json`
- entry ID uniqueness
- entry path uniqueness
- entry path relative safety (no absolute paths, no `..` traversal)
- dependency graph validation:
  - dependency references must resolve
  - cycles are forbidden

## 9) Version Compatibility Semantics

- `minSystemVersion` and `maxTestedSystemVersion` must be valid `X.Y.Z`.
- `minSystemVersion <= maxTestedSystemVersion` is required.
- Hard fail when `minSystemVersion > currentSystemVersion`.
- Soft warning when `currentSystemVersion > maxTestedSystemVersion`.

## 10) Balance Calibration Gate (Phase 2)

- Derived HP/Spirit calibration checks compare deterministic derived values to baseline midpoint targets per sequence.
- Gate modes:
  - `warn`: log findings, do not fail
  - `strict`: fail on out-of-band findings
  - `off`: skip calibration check
- Default gate mode is read from `system-config-v1.1.json.validation.gates.balanceGateMode`.

## 11) Migration Compatibility

- v1 content must remain importable.
- v1.1 hardening fields follow strict validation in v1.1-targeted packs.
- Migration into v1.1 must inject/normalize required semantics before publish.

## 12) Publish Gate

A package can be published only if all are true:
1. Schema validation passes.
2. Registry checks pass.
3. Formula checks pass.
4. Item/effect semantic checks pass.
5. Manifest checks pass.
6. Version compatibility semantics pass.
7. Verification vectors pass.

## 13) Compendium-First Source Contract (v1.2+)

- Canonical authoring source lives in `content-src/<domain>/*.json`.
- Generated Foundry compendium databases in `packs/*.db` are build artifacts and must be deterministic.
- Every content entry must declare:
  - `id`
  - `pack`
  - `documentType` (`Item`, `RollTable`, `Actor`, `JournalEntry`)
  - `name`
  - `version`
  - `minSystemVersion`
  - `maxTestedSystemVersion`
  - `dependencies[]`
- Cross-entry dependencies must resolve to known IDs.
- Pack generation must preserve stable document identity (`_id`) for update-safe migrations.
