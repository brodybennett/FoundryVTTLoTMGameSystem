# Foundry Schema Contract v1.1

This document defines additive v1.1 contract extensions over v1, plus Phase 1 blocker hardening required for a prototype-ready rules engine.

## Scope

- Target: Foundry DataModel-style architecture (v12+).
- Automation boundary: hybrid.
- Compatibility target: v1 content remains valid.

## Required Schema Files (v1.1)

- `schemas/actor.system.schema.v1_1.json`
- `schemas/item.system.schema.v1_1.json`
- `schemas/effect.schema.v1_1.json`
- `schemas/content.pack.manifest.schema.v1_1.json`
- `schemas/content.rolltable.schema.v1_2.json`

## Additive Actor.system Fields

Optional:
- `combat.armor`
- `combat.cover`
- `combat.encumbrancePenalty`
- `combat.damageReduction`
- `combat.actionBudget.{actions,moves,reactions,bonusActions}`
- `tracks.threatClocks[]`
- `tracks.influence`
- `tracks.leverage`
- `tracks.actionLock`
- `tracks.movementCheckPenalty`
- `tracks.damageOutMultiplier`
- `tracks.incomingOffenseBonus`
- `tracks.offensePenaltyVsSource`
- `tracks.verbalLocked`
- `tracks.markedBySourceBonus`
- `tracks.isDowned`
- `ritual.instability`
- `artifacts.sceneUsesById`

Required resource additions:
- `resources.deathSaves`

Required creation contract:
- `creation.state`
- `creation.completedSteps[]`
- `creation.version`

## Item.system Hardening Rules

Optional:
- `allowedPathwayIds[]`
- `usageLimit.{scope,maxUses}`
- `complexityClass`
- `sourceSequence`
- typed payload blocks:
  - `abilityData`
  - `weaponData`
  - `armorData`
  - `ritualData`
  - `artifactData`

Required on all item entries:
- `dependencies.minSystemVersion`
- `dependencies.maxTestedSystemVersion`

Semantic constraints:
- For `type: ability`, `minSequence <= sequence`.
- If both `pathwayId` and `allowedPathwayIds[]` are present, `allowedPathwayIds[]` must include `pathwayId`.
- `formulaKey` is registry-driven and validated against `system-config-v1.1.json.formulaRegistry`.
- `type: ability` requires `abilityData`.
- `type: weapon` requires `weaponData`.
- `type: armor` requires `armorData`.
- `type: ritual` requires `ritualData`.
- `type: artifact` requires `artifactData`.

## Effect Hardening Rules

Required:
- `sourceCategory`
- `target`
- `trigger`

Optional:
- `stackGroup`
- `oncePerTurn`

Semantic constraints:
- If `saveType = none`, then `saveTarget = 0` and `removeOn` must not include `saveSuccess`.
- If `saveType != none`, `saveTarget` must be `1..95`.
- If `op = cost`, `value` must be non-negative.

## Registry Files

- `data/skills.registry.v1.1.json`
- `data/conditions.library.v1.1.json`

Registry policy:
- canonical required IDs are mandatory
- additional IDs are allowed when schema-valid and unique

## Manifest Requirement

Published compendium packs must include a manifest conforming to:

- `schemas/content.pack.manifest.schema.v1_1.json`

Manifest hardening rules:
- entry IDs must be unique within pack
- entry paths must be unique within pack
- entry paths must be relative and must not contain `..` traversal segments

## Versioning and Migration Rules

- v1 and v1.1 objects may coexist.
- Major incompatibility remains a hard reject.
- Migration scripts must be one-way and idempotent.
- Semver ordering is enforced for `minSystemVersion` and `maxTestedSystemVersion`.
- Dependency graphs for published manifests must be acyclic and fully resolvable.

## Phase 2 Balance Calibration Gate

- Derived HP/Spirit calibration is validated against baseline midpoint targets per sequence.
- Gate mode is configured by `system-config-v1.1.json.validation.gates.balanceGateMode`.
- Supported modes:
  - `warn`
  - `strict`
  - `off`

## Foundry Package Runtime and Packs (v1.2)

- `system.json.packs[]` is required for published gameplay content.
- Packs are system-owned (`lotm-system.<pack-name>`) and resolve to `packs/<pack-name>.db`.
- Content is authored in `content-src/` and compiled into `packs/*.db`.
- Pack and content IDs are immutable once published.
- Semver compatibility is enforced per content entry:
  - hard-fail when `minSystemVersion > current system version`
  - hard-fail when `minSystemVersion > maxTestedSystemVersion`
  - warning when `current system version > maxTestedSystemVersion`

## RollTable Runtime Contract (v1.2.2)

- Roll table source content conforms to `schemas/content.rolltable.schema.v1_2.json`.
- Segment enum is locked to:
  - `resources`
  - `abilities`
  - `rituals`
  - `artifacts`
  - `corruption`
  - `encounters`
- Runtime API exposes:
  - `game.lotm.rollOnSegment(segment, context={})`
  - `game.lotm.rollOnTableId(contentId, context={})`
- Hook routing comes from automation mapping:
  - ritual failure -> `rituals`
  - artifact backlash -> `artifacts`
  - corruption threshold cross -> `corruption`
