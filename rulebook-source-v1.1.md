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

## 2. Action Economy

Per turn:
- 1 Action
- 1 Move
- 1 Reaction per round

There is no universal Bonus Action. A bonus action exists only if an ability explicitly grants it.

## 3. Skills and Proficiency

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

## 4. Corruption

```text
CorruptionPenalty = max(-6, -1 * floor(CurrentCorruptionPct / 10))
```

Mandatory trigger thresholds are `30%`, `60%`, `90%`, `100%`.

## 5. Ability Data Contract (Schema-Aligned)

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

## 6. Sequence Gate Semantics

Lower sequence numbers are stronger (`9 -> 0`).

An ability may be used when:
- pathway permission is valid, and
- `actor.sequence <= ability.minSequence`

For abilities, content must satisfy:
- `ability.minSequence <= ability.sequence`
- if `allowedPathwayIds` exists, it must include `ability.pathwayId`

## 7. Ritual Corruption Term (Hardening)

Corruption applies as a penalty term in ritual checks:

```text
RitualTarget = clamp(
  35 + floor((WIL + INT + LUCK) / 3) + RitualProficiency - Complexity + CorruptionPenalty + CircleBonuses,
  1,
  95
)
```

`CorruptionPenalty` is non-positive, so this term cannot increase ritual success chance.

## 8. Effect Lifecycle Safety

For effect entries:
- `sourceCategory` is required.
- if `saveType = none`, `saveTarget` must be `0` and `removeOn` cannot contain `saveSuccess`.
- if `saveType != none`, `saveTarget` must be `1..95`.
- if `op = cost`, `value` must be non-negative.

## 9. Manifest Publish Safety

Manifest entries must satisfy:
- unique `id`
- unique `path`
- relative path only, with no `..` traversal segments
