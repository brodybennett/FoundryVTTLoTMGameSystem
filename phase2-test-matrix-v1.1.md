# Phase 2 Test Matrix v1.1

## Schema Compatibility

1. v1.1 actor tracks include all condition-targeted keys (`actionLock`, `movementCheckPenalty`, `damageOutMultiplier`, `incomingOffenseBonus`, `offensePenaltyVsSource`, `verbalLocked`, `markedBySourceBonus`, `isDowned`).
2. v1.1 actor resources include `deathSaves`.
3. v1.1 actor combat contract includes `armor`, `cover`, `encumbrancePenalty`, `damageReduction`, and `actionBudget`.
4. v1.1 item contract requires `dependencies`.
5. Corruption contracts include explicit `penaltyBands` through `90-100 => -10`.
6. Validation gates include `validation.gates.balanceGateMode` with `warn|strict|off`.
4. `formulaKey` is pattern-based and validated against runtime registry.
7. v1.1 effect contract requires `sourceCategory`, `target`, and `trigger`.
8. Effect save semantics enforce:
   - `saveType = none` => `saveTarget = 0` and no `removeOn: saveSuccess`
   - `saveType != none` => `saveTarget` in `1..95`
9. `op = cost` enforces non-negative value.
10. Type payload requirements enforce:
   - `ability` -> `abilityData`
   - `weapon` -> `weaponData`
   - `armor` -> `armorData`
   - `ritual` -> `ritualData`
   - `artifact` -> `artifactData`

## Registry Tests

1. Skill registry contains required canonical skill IDs with canonical linked attributes.
2. Skill registry permits additional IDs when valid and unique.
3. Conditions library contains required canonical condition IDs.
4. Conditions library permits additional IDs when valid and unique.
5. Condition effects are lifecycle-complete and satisfy semantic safety rules.
6. Condition effects only target whitelisted paths and schema-defined `system.tracks.*` keys.

## Item Semantic Tests

1. Ability with `minSequence > sequence` fails.
2. Ability with `allowedPathwayIds` excluding `pathwayId` fails.
3. Ability with unknown `formulaKey` fails.
4. Missing `dependencies` fails.
5. Invalid semver format fails.
6. `minSystemVersion > maxTestedSystemVersion` fails.
7. `minSystemVersion > currentSystemVersion` fails.
8. `currentSystemVersion > maxTestedSystemVersion` warns under soft gate.

## Manifest Tests

1. Valid manifest passes required field checks.
2. Invalid schema target fails.
3. Empty entries list fails.
4. Duplicate entry IDs fail.
5. Duplicate entry paths fail.
6. Unsafe relative path (`..`) fails.
7. Invalid manifest semver format fails.
8. `minSystemVersion > maxTestedSystemVersion` fails.
9. Dependency reference missing target pack fails.
10. Dependency cycle fails.
11. `currentSystemVersion > maxTestedSystemVersion` warns under soft gate.

## Balance Calibration Tests

1. Corruption boundary checks:
   - `59 -> -5`, `60 -> -6`, `69 -> -6`, `70 -> -7`, `89 -> -8`, `90 -> -10`, `100 -> -10`.
2. Derived HP/Spirit calibration computes per-sequence deltas against baseline midpoint targets.
3. Gate mode behavior:
   - `warn`: logs findings and continues
   - `strict`: fails on out-of-band findings
   - `off`: skips calibration

## Acceptance

1. `python scripts/phase2_verification.py` passes.
2. `python scripts/phase1_verification.py` passes.
