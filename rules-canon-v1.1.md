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
CorruptionPenalty = lookupBandPenalty(CurrentCorruptionPct)
```

with locked penalty bands:
- `0-9 => 0`
- `10-19 => -1`
- `20-29 => -2`
- `30-39 => -3`
- `40-49 => -4`
- `50-59 => -5`
- `60-69 => -6`
- `70-79 => -7`
- `80-89 => -8`
- `90-100 => -10`

4. Combat attack and damage pipeline is:

```text
AttackTarget = clamp(35 + floor(AttackAttribute / 3) + ProficiencyBonus + OffenseModifiers + WeaponAccuracy - TargetDefenseShift - TargetCoverPenalty, 1, 95)
FinalDamage = max(1, floor((BaseDamage + FlatDamageBonus) * DamageOutMultiplier) - TargetDamageReduction)
```

5. Action economy is:
- `1 Action`
- `1 Move`
- `1 Reaction` per round
- no universal bonus action

6. Downed/death track uses:
- `check.death.v1`
- `resources.deathMarks` and `resources.deathSaves`
- 3 marks = death, 3 saves = stabilize

7. Advancement remains 3-stage with natural 1 margin bonus and natural 100 backlash flag.
- Channeling uses `willpower` by default, or `endurance` if declared before rolling.
- Failure penalties apply flat corruption points on the `0..100` track.

8. Ritual checks apply corruption as a penalty term:

```text
RitualTarget = ... + CorruptionPenalty ...
```

where `CorruptionPenalty <= 0`.

## v1.1 Additive Contract Additions

### Actor.system Optional
- `tracks.threatClocks`
- `tracks.influence`
- `tracks.leverage`
- `combat.armor`
- `combat.cover`
- `combat.encumbrancePenalty`
- `combat.damageReduction`
- `combat.actionBudget`
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

### Actor.system Required Resource Additions
- `resources.deathSaves`

### Item.system Optional
- `allowedPathwayIds`
- `usageLimit.{scope,maxUses}`
- `complexityClass`
- `sourceSequence`
- type payload blocks:
  - `abilityData`
  - `weaponData`
  - `armorData`
  - `ritualData`
  - `artifactData`

### Item.system Required Hardening
- `dependencies.minSystemVersion`
- `dependencies.maxTestedSystemVersion`
- ability semantic constraints:
  - `minSequence <= sequence`
  - if both `pathwayId` and `allowedPathwayIds` are present, `allowedPathwayIds` must include `pathwayId`
  - `formulaKey` must resolve through runtime formula registry

### Effect Hardening
- `sourceCategory` required
- `target` required
- `trigger` required
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
