# Migration Guide: v1 -> v1.1

## Compatibility Model

- v1 content remains valid.
- v1.1 introduces semantic hardening for published packs.

## Actor Migration

Defaults added when absent:
- `tracks.threatClocks = []`
- `tracks.influence = {}`
- `tracks.leverage = {}`
- `ritual.instability = 0`
- `artifacts.sceneUsesById = {}`

## Item Migration

Required for v1.1-targeted publish entries:
- `dependencies.minSystemVersion`
- `dependencies.maxTestedSystemVersion`

When present, these v1.1 fields are additionally validated:
- `allowedPathwayIds`
- `usageLimit`
- `complexityClass`
- `sourceSequence`

Ability semantic checks:
- `minSequence <= sequence`
- if both `allowedPathwayIds` and `pathwayId` exist, list must include `pathwayId`
- `formulaKey` must resolve in runtime formula registry

## Effect Migration

Required for v1.1-targeted publish effects:
- `sourceCategory`

Optional v1.1 controls:
- `stackGroup`
- `oncePerTurn`

Semantic checks:
- `saveType = none` requires `saveTarget = 0` and forbids `removeOn: saveSuccess`
- `saveType != none` requires `saveTarget` in `1..95`
- `op = cost` requires non-negative `value`

## Command Examples

Dry-run idempotence check:

```powershell
python scripts/migrate_v1_to_v1_1.py --dry-run
```

Apply migration to file:

```powershell
python scripts/migrate_v1_to_v1_1.py --input actor.system.json --output actor.system.v1_1.json
```
