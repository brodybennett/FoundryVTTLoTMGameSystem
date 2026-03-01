# LORD OF THE MYSTERIES TTRPG
## Canonical Rulebook Source v1.1

### Canonical Precedence (v1.1)
If this prose conflicts with `system-config-v1.1.json`, `core-tables-v1.csv`, or `schemas/*.v1_1.json`, those machine-readable files are authoritative for implementation.

## 1. Core Check System

All core checks use 1d100 roll-under.

```text
FinalTarget = clamp(BaseTarget + Modifiers - Penalties, 1, 95)
Success if roll <= FinalTarget
Critical success: natural 1
Critical failure: natural 100
Margin = abs(FinalTarget - roll)
```

## 2. Combat Resolution Pipeline

Attack checks and damage are resolved in this order:

```text
AttackTarget = clamp(
  35 + floor(AttackAttribute / 3) + ProficiencyBonus + OffenseModifiers + WeaponAccuracy - TargetDefenseShift - TargetCoverPenalty,
  1,
  95
)
```

If attack roll succeeds, resolve damage:

```text
FinalDamage = max(1, floor((BaseDamage + FlatDamageBonus) * DamageOutMultiplier) - TargetDamageReduction)
```

Critical handling:
- natural 1 on attack: critical hit, double `BaseDamage` before additive and multiplicative steps
- natural 100 on attack: automatic miss

## 3. Action Economy

Per turn:
- 1 Action
- 1 Move
- 1 Reaction per round

There is no universal Bonus Action. A bonus action exists only if an ability explicitly grants it.

## 4. Skills and Proficiency

```text
SkillTarget = clamp(
  25 + floor(LinkedAttribute / 3) + ProficiencyBonus + floor(LUCK / 10) + SituationalModifiers - SituationalPenalties,
  1,
  95
)
```

Passive rating:

```text
PassiveRating = floor(SkillTarget / 2)
```

## 5. Corruption

```text
CorruptionPenalty = lookupBandPenalty(CurrentCorruptionPct)
```

Penalty bands:
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

Mandatory trigger thresholds are `30%`, `60%`, `90%`, `100%`.

Corruption is tracked in integer points from `0` to `100`.

## 6. Downed and Death Track

When a character reaches `HP <= 0`:
- set `HP = 0`
- apply `condition.downed`
- set `deathSaves = 0`

At end of each of the downed character's turns, roll:

```text
DeathTarget = clamp(50 + floor(CON / 2) - min(6, floor(CorruptionPct / 10)), 1, 95)
```

Outcomes:
- success: gain 1 death save
- failure: gain 1 death mark
- natural 1: gain 2 death saves
- natural 100: gain 2 death marks

Resolution:
- at `3 death saves`: character stabilizes (remains unconscious at 0 HP, no further death checks)
- at `3 death marks`: character dies
- if a downed character takes damage: gain `1 death mark`
- any healing that raises HP above 0 removes downed and resets death marks and death saves to 0

## 7. Advancement Resolution

Advancement uses three stages:
- preparation: `ritualism`
- channeling: `willpower` by default, or `endurance` if declared before rolling
- integration: `ritualism`

Natural 1 and natural 100 apply universal critical rules:
- natural 1: success and `+10` margin bonus
- natural 100: stage auto-fails and triggers backlash check

Advancement failure penalties apply corruption points directly on the `0..100` corruption track:
- one pass total: `+8 corruption`, consume `50%` ingredients
- zero passes: `+15 corruption`, consume `100%` ingredients
- critical backlash: `+25 corruption`, consume `100%` ingredients, consume one extra rare-equivalent ingredient, trigger corruption event

## 8. Ability Data Contract (Schema-Aligned)

All published abilities must align to `schemas/item.system.schema.v1_1.json`.

```json
{
  "id": "ability.seer.hunch_of_danger",
  "schemaVersion": 1,
  "name": "Hunch of Danger",
  "type": "ability",
  "pathwayId": "pathway.seer",
  "sequence": 9,
  "minSequence": 9,
  "activation": "reaction",
  "resource": "spirit",
  "cost": 6,
  "cooldown": 1,
  "formulaKey": "check.skill.v1",
  "effects": [],
  "allowedPathwayIds": ["pathway.seer"],
  "usageLimit": {
    "scope": "perRound",
    "maxUses": 1
  },
  "dependencies": {
    "minSystemVersion": "1.1.0",
    "maxTestedSystemVersion": "1.1.0"
  }
}
```

## 9. Sequence Gate Semantics

Lower sequence numbers are stronger (`9 -> 0`).

An ability may be used when:
- pathway permission is valid, and
- `actor.sequence <= ability.minSequence`

For abilities, content must satisfy:
- `ability.minSequence <= ability.sequence`
- if `allowedPathwayIds` exists, it must include `ability.pathwayId`

## 10. Ritual Corruption Term (Hardening)

Corruption applies as a penalty term in ritual checks:

```text
RitualTarget = clamp(
  35 + floor((WIL + INT + LUCK) / 9) + RitualProficiency - Complexity + CorruptionPenalty + CircleBonuses,
  1,
  95
)
```

`CorruptionPenalty` is non-positive, so this term cannot increase ritual success chance.

## 11. Effect Lifecycle Safety

For effect entries:
- `sourceCategory` is required.
- `target` is required.
- `trigger` is required.
- if `saveType = none`, `saveTarget` must be `0` and `removeOn` cannot contain `saveSuccess`.
- if `saveType != none`, `saveTarget` must be `1..95`.
- if `op = cost`, `value` must be non-negative.

## 12. Manifest Publish Safety

Manifest entries must satisfy:
- unique `id`
- unique `path`
- relative path only, with no `..` traversal segments
