# Phase 2 Test Matrix v1.1

## Schema Compatibility

1. v1 actor object validates under v1 and remains accepted in migration.
2. v1.1 actor tracks include all condition-targeted keys (`actionLock`, `movementCheckPenalty`, `damageOutMultiplier`, `incomingOffenseBonus`, `offensePenaltyVsSource`, `verbalLocked`, `markedBySourceBonus`, `isDowned`).
3. v1 item object validates under v1.1 unchanged.
4. v1.1 item contract requires `dependencies`.
5. `formulaKey` is pattern-based and validated against runtime registry.
6. v1.1 effect contract requires `sourceCategory`.
7. Effect save semantics enforce:
   - `saveType = none` => `saveTarget = 0` and no `removeOn: saveSuccess`
   - `saveType != none` => `saveTarget` in `1..95`
8. `op = cost` enforces non-negative value.

## Registry Tests

1. Skill registry contains required canonical skill IDs.
2. Conditions library contains required canonical condition IDs.
3. Condition effects are lifecycle-complete and satisfy semantic safety rules.
4. Condition effects only target whitelisted paths and schema-defined `system.tracks.*` keys.

## Item Semantic Tests

1. Ability with `minSequence > sequence` fails.
2. Ability with `allowedPathwayIds` excluding `pathwayId` fails.
3. Ability with unknown `formulaKey` fails.
4. Missing `dependencies` fails.

## Manifest Tests

1. Valid manifest passes required field checks.
2. Invalid schema target fails.
3. Empty entries list fails.
4. Duplicate entry IDs fail.
5. Duplicate entry paths fail.
6. Unsafe relative path (`..`) fails.

## Migration Tests

1. v1 -> v1.1 migration backfills defaults.
2. Re-running migration is idempotent.
3. Migration report includes upgraded/defaulted field counters.

## Acceptance

1. `python scripts/phase2_verification.py` passes.
2. `python scripts/migrate_v1_to_v1_1.py --dry-run` passes idempotence checks.
3. `python scripts/phase1_verification.py` still passes unchanged vectors.
