# Content Validation Rules v1

This file defines the compendium-first governance and validation gates for LoTM Canon v1.

## 1) Required Metadata

Every content entry must include:

- `id` (immutable, namespaced slug: `namespace.type.slug`)
- `schemaVersion` (integer)
- `name`
- `type`
- `dependencies.minSystemVersion`
- `dependencies.maxTestedSystemVersion`

Content without this metadata is invalid.

## 2) ID and Reference Rules

- IDs must match: `^[a-z][a-z0-9_.-]*$`
- IDs are immutable once released.
- Referenced IDs (`pathwayId`, `requiresIds`, condition IDs) must exist at import time.
- Circular hard dependencies are invalid.

## 3) Enum and Numeric Rules

- Enum values must match schema exactly.
- Out-of-range numerics are rejected:
  - targets: `1..95`
  - sequence: `0..9`
  - corruption pct: `0..100`
  - cooldown/cost: non-negative
- Unknown enum values are hard errors.

## 4) Ability-Specific Rules

For `type = ability`, required:

- `pathwayId`
- `sequence`
- `minSequence`
- `activation`
- `resource`
- `cost`
- `cooldown`
- `formulaKey`
- `effects[]`

Additional checks:

- `formulaKey` must be in registry.
- `effects[]` operations must be one of: `add`, `mul`, `set`, `grantCondition`, `cost`.
- `minSequence` and `sequence` relationship must be coherent with the source node.

## 5) Effect Lifecycle Rules

Every effect must define:

- `applyPhase`
- `tickPhase`
- `durationRounds`
- `saveType`
- `saveTarget`
- `stackRule`
- `removeOn`

Rules:

- If `saveType = none`, `saveTarget` must be `0`.
- If `op = grantCondition`, `conditionId` is required.
- If `op` is numeric mutation (`add/mul/set/cost`), `path` and `value` are required.

## 6) Versioning and Migration Rules

- Major version mismatch: reject import.
- Minor/patch mismatch: allow with warning if schemas are backward compatible.
- Migration scripts must be idempotent and logged.
- Deprecated fields require explicit migration map before release.

## 7) Lint Severity

- Error: blocks import/package publish.
- Warning: package import allowed in dev mode only.
- Info: style guidance only.

## 8) Publish Gate

A compendium package can be published only if all are true:

1. Schema validation passes.
2. Reference/dependency validation passes.
3. Formula registry validation passes.
4. Required test vectors pass.
5. Version compatibility metadata is present.

## 9) Governance Defaults

- Dual-pathway content is disallowed by default in v1 packs.
- Narrative-only effects must still provide machine-safe structural fields.
- No executable script payloads are permitted in content entries.
