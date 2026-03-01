# Authoring Cookbook v1.1

## Purpose

Guide content authors to produce pack entries that validate under v1.1 without code changes.

## Authoring Rules

1. Use immutable IDs (`namespace.type.slug`).
2. Keep `schemaVersion: 1` for v1 and v1.1 content objects.
3. Always include dependency versions:
- `dependencies.minSystemVersion`
- `dependencies.maxTestedSystemVersion`
4. Use only formula keys defined in `system-config-v1.1.json.formulaRegistry`.
5. Keep effect paths within whitelist prefixes.
6. If `type: ability`, ensure `minSequence <= sequence`.
7. If both `pathwayId` and `allowedPathwayIds` are present, include `pathwayId` in `allowedPathwayIds`.

## Ability Example Checklist

- `type: ability`
- `pathwayId`
- `sequence`
- `minSequence`
- `activation`
- `resource`
- `cost`
- `cooldown`
- `formulaKey`
- `effects[]`

## Condition Authoring

For every effect:
- provide complete lifecycle fields
- provide `path/value` for numeric mutations
- always set `sourceCategory`
- use `stackGroup` when stacking must be controlled
- use `oncePerTurn` for periodic/tick safety
- if `saveType: none`, set `saveTarget: 0` and do not use `removeOn: saveSuccess`
- if `saveType` is not `none`, set `saveTarget` in `1..95`
- for `op: cost`, use non-negative `value`

## Manifest Authoring

For every pack manifest:
- entry `id` values must be unique
- entry `path` values must be unique
- entry paths must be relative and cannot contain `..`

## Pack Publish Checklist

1. Validate entries against schema.
2. Validate references and dependencies.
3. Validate semantic constraints (sequence gating, pathway permissions, effect lifecycle).
4. Validate manifest schema and uniqueness/path safety rules.
5. Run Phase 1/2 verification scripts.
6. Run consolidated verification gate.
