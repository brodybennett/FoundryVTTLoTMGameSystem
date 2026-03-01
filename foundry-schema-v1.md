# Foundry Schema Contract v1

This document defines the minimum data contract for the LoTM Canon v1 prototype.

## Scope

- Target: Foundry DataModel-style architecture (v12+ patterns).
- Automation boundary: hybrid.
  - Automated: deterministic math, state tracking, cooldown/resource spend, corruption bands, death marks, initiative sorting.
  - GM-managed: narrative gates, story consequences, clue interpretation, major corruption event narrative outcomes.

## Required Schema Files

- `schemas/actor.system.schema.v1.json`
- `schemas/item.system.schema.v1.json`
- `schemas/effect.schema.v1.json`

## Formula Registry Keys (Required)

- `check.attribute.v1`
- `check.skill.v1`
- `check.ritual.v1`
- `check.death.v1`
- `calc.derived.hp.v1`
- `calc.derived.spirit.v1`
- `calc.derived.sanity.v1`
- `calc.corruption.penalty.v1`

## Actor.system Required Fields

- `identity.pathwayId`
- `identity.sequence`
- `identity.tier`
- `attributes.{str,dex,wil,con,cha,int,luck}.{base,temp}`
- `skills.<id>.{linkedAttr,rank,misc}`
- `derived.{hpMax,spiritMax,sanityMax,defenseShift,initiativeTarget}`
- `resources.{hp,spirit,corruption,deathMarks}`
- `progression.gates.{narrative,economy,stability}`
- `version.schemaVersion`

## Item Types (Allowed)

- `pathway`
- `sequenceNode`
- `ability`
- `ritual`
- `artifact`
- `weapon`
- `armor`
- `consumable`
- `ingredient`
- `background`
- `conditionTemplate`

## Ability Required Fields

- `id`
- `schemaVersion`
- `name`
- `type` (`ability`)
- `pathwayId`
- `sequence`
- `minSequence`
- `activation`
- `resource`
- `cost`
- `cooldown`
- `formulaKey`
- `effects[]`

## Condition / Effect Lifecycle Contract

Every effect entry in `effects[]` must conform to:

- `applyPhase`
- `tickPhase`
- `durationRounds`
- `saveType`
- `saveTarget`
- `stackRule`
- `removeOn`

Supported operation model:

- `add`
- `mul`
- `set`
- `grantCondition`
- `cost`

## Versioning and Migration Contract

- Every Actor and Item entry must include `schemaVersion`.
- System runtime must reject content with incompatible major version.
- All migration scripts are one-way and idempotent.
- Content pack manifests must declare `minSystemVersion` and `maxTestedSystemVersion`.

## Import/Export Safety Rules

- Reject unknown enum values.
- Reject references to non-existent pathway/sequence IDs.
- Reject ability entries without `formulaKey`.
- Reject `minSequence` weaker than `sequence` source semantics.
- Reject numeric fields outside declared caps.
