# Foundry Schema Contract v1.1

This document defines additive v1.1 contract extensions over v1, plus anti-exploit hardening rules.

## Scope

- Target: Foundry DataModel-style architecture (v12+).
- Automation boundary: hybrid.
- Compatibility target: v1 content remains valid.

## Required Schema Files (v1.1)

- `schemas/actor.system.schema.v1_1.json`
- `schemas/item.system.schema.v1_1.json`
- `schemas/effect.schema.v1_1.json`
- `schemas/content.pack.manifest.schema.v1_1.json`

## Additive Actor.system Fields

Optional:
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

## Item.system Hardening Rules

Optional:
- `allowedPathwayIds[]`
- `usageLimit.{scope,maxUses}`
- `complexityClass`
- `sourceSequence`

Required on all item entries:
- `dependencies.minSystemVersion`
- `dependencies.maxTestedSystemVersion`

Semantic constraints:
- For `type: ability`, `minSequence <= sequence`.
- If both `pathwayId` and `allowedPathwayIds[]` are present, `allowedPathwayIds[]` must include `pathwayId`.
- `formulaKey` is registry-driven and validated against `system-config-v1.1.json.formulaRegistry`.

## Effect Hardening Rules

Required:
- `sourceCategory`

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
