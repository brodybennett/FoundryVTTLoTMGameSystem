# LoTM Canon v1.1 - Phase 1 Through 3 Completion Baseline

Status: Active implementation baseline for Foundry prototype and content expansion  
Scope: Includes blocker closure, additive schema contracts, publish pipeline  
Profile: Gritty parity combat (6-9 rounds), hybrid automation

## Canonical Precedence

If prose conflicts with:
- `system-config-v1.1.json`
- `core-tables-v1.csv`
- `schemas/*.v1_1.json`

those files are authoritative for v1.1 implementation.

## Locked Rules (Carry Forward)

1. Universal target clamp is `1..95`.
2. Skill target formula is:

```text
25 + floor(LinkedAttribute / 3) + ProficiencyBonus + floor(LUCK / 10)
```

3. Corruption penalty is:

```text
CorruptionPenalty = max(-6, -1 * floor(CurrentCorruptionPct / 10))
```

4. Action economy is:
- `1 Action`
- `1 Move`
- `1 Reaction` per round
- no universal bonus action

5. Advancement remains 3-stage with natural 1 margin bonus and natural 100 backlash flag.
6. Ritual checks apply corruption as a penalty term:

```text
RitualTarget = ... + CorruptionPenalty ...
```

where `CorruptionPenalty <= 0`.

## v1.1 Additive Contract Additions

### Actor.system Optional
- `tracks.threatClocks`
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

### Item.system Optional
- `allowedPathwayIds`
- `usageLimit.{scope,maxUses}`
- `complexityClass`
- `sourceSequence`

### Item.system Required Hardening
- `dependencies.minSystemVersion`
- `dependencies.maxTestedSystemVersion`
- ability semantic constraints:
  - `minSequence <= sequence`
  - if both `pathwayId` and `allowedPathwayIds` are present, `allowedPathwayIds` must include `pathwayId`
  - `formulaKey` must resolve through runtime formula registry

### Effect Hardening
- `sourceCategory` required
- `stackGroup`
- `oncePerTurn`
- `saveType = none` requires `saveTarget = 0` and forbids `removeOn: saveSuccess`
- `saveType != none` requires `saveTarget` in `1..95`
- `op = cost` requires non-negative `value`

### New Required Publish Manifest

Published compendium packs must include manifest metadata conforming to:

- `schemas/content.pack.manifest.schema.v1_1.json`

and semantic publish checks:
- entry `id` uniqueness
- entry `path` uniqueness
- entry path safety (relative only, no `..` traversal)

### Canonical Registry Files

- `data/skills.registry.v1.1.json`
- `data/conditions.library.v1.1.json`
