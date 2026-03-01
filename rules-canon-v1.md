# LoTM Canon v1 - Phase 1 Blocker Resolution

Status: Frozen baseline for Foundry prototype implementation  
Scope: Blocker-level rules only (no new content expansion)  
Profile: Gritty parity combat (6-9 rounds), hybrid automation

## Global Definitions

- Sequence order: `9 -> 0` (lower number is stronger).
- Tier mapping:
  - `9-8 = low`
  - `7-6 = mid`
  - `5 = high`
  - `4-2 = demigod`
  - `1 = angel`
  - `0 = god`
- `withinTierIndex` is the 0-based index of the sequence inside its tier bucket:
  - `9:0, 8:1, 7:0, 6:1, 5:0, 4:0, 3:1, 2:2, 1:0, 0:0`

## 2.1 Dice & Resolution (Canonical Replacement)

### Universal Check Algorithm

```text
Inputs:
  BaseTarget
  Modifiers (sum of positive shifts)
  Penalties (sum of negative shifts)

FinalTarget = clamp(BaseTarget + Modifiers - Penalties, 1, 95)
Roll = 1d100

If Roll == 1: Critical Success
Else if Roll == 100: Critical Failure
Else if Roll <= FinalTarget: Success
Else: Failure

Margin = abs(FinalTarget - Roll)
```

### Outcome Tiers

- Critical Success: natural `1`
- Strong Success: success with margin `20+`
- Standard Success: success with margin `1-19`
- Standard Failure: failure with margin `1-19`
- Severe Failure: failure with margin `20+`
- Critical Failure: natural `100`

### Contested Checks (Canonical Tie-Break Order)

1. If one side succeeds and the other fails, success wins.
2. If both succeed, higher success margin wins.
3. If both fail, lower failure margin wins.
4. If tied, higher `BaseTarget` wins.
5. If tied, lower sequence number wins.
6. If tied, higher `LUCK` wins.
7. If tied, reroll.

### Group Checks

- Lead actor rolls one final check.
- Up to 3 helpers can contribute.
- Each helper with success margin `10+` adds `+5` to lead (max `+15` total).
- If 2 or more helpers severely fail, GM applies a complication even on lead success.

## 2.3 Skills & Proficiency (Canonical Replacement)

### Skill Target Formula

```text
SkillTarget = clamp(
  25 + floor(LinkedAttribute / 3) + ProficiencyBonus + floor(LUCK / 10) + SituationalModifiers - SituationalPenalties,
  1,
  95
)
```

### Proficiency Bonuses

- Untrained: `+0`
- Familiar: `+5`
- Trained: `+10`
- Expert: `+15`
- Master: `+20`
- Legendary: `+25`

### Passive Rating

```text
PassiveRating = floor(SkillTarget / 2)
```

Use passive only when there is no immediate time pressure and no active opposition.  
If an unaware defender is opposed by an active actor, resolve `Active vs Passive`.

## 2.4 Derived Statistics (Canonical Replacement)

### Health

```text
HealthCore = 20 + (STR * 1.5) + (CON * 2.5)
HealthSeqMult = TierHealthBase[tier] * (TierHealthStep[tier] ^ withinTierIndex)
MaxHealth = round(HealthCore * HealthSeqMult)
```

Tier multipliers:

- low: base `1.00`, step `1.06`
- mid: base `1.25`, step `1.09`
- high: base `1.60`, step `1.00`
- demigod: base `2.15`, step `1.12`
- angel: base `3.05`, step `1.00`
- god: base `4.40`, step `1.00`

### Spirit

```text
SpiritCore = 15 + (WIL * 2.2) + (INT * 1.2) + floor(LUCK / 4)
SpiritSeqMult = TierSpiritBase[tier] * (TierSpiritStep[tier] ^ withinTierIndex)
MaxSpirit = round(SpiritCore * SpiritSeqMult)
```

Tier multipliers:

- low: base `1.00`, step `1.06`
- mid: base `1.30`, step `1.10`
- high: base `1.75`, step `1.00`
- demigod: base `2.35`, step `1.13`
- angel: base `3.30`, step `1.00`
- god: base `4.85`, step `1.00`

### Sanity / Corruption Threshold

```text
SanityCore = 30 + (WIL * 1.8) + (CON * 1.1) + floor(LUCK / 5)
SanitySeqMult = TierSanityBase[tier] * (TierSanityStep[tier] ^ withinTierIndex)
MaxSanity = round(SanityCore * SanitySeqMult)
```

Tier multipliers:

- low: base `1.00`, step `1.05`
- mid: base `1.18`, step `1.07`
- high: base `1.45`, step `1.00`
- demigod: base `1.90`, step `1.10`
- angel: base `2.55`, step `1.00`
- god: base `3.60`, step `1.00`

### Recovery (Corrected)

- Short Rest: `round(MaxHealth * 0.45)` HP and `round(MaxSpirit * 0.45)` Spirit.
- Long Rest: restore to full unless blocked by active injury/corruption lock.

### Corruption Penalty (Unified)

```text
CorruptionPenalty = max(-6, -1 * floor(CurrentCorruptionPct / 10))
```

Mandatory escalation triggers: `30%`, `60%`, `90%`, `100%`  
Band crossing applies immediately.

### Defense & Initiative

```text
RawDefenseShift = floor((DEX + CON - 20) / 8) + Armor + Cover + Effects
DefenseShift = clamp(RawDefenseShift, -20, 25)

InitiativeTarget = clamp(
  20 + floor((DEX * 0.5) + (INT * 0.35) + (LUCK * 0.15))
  + SequenceEdgeBonus - EncumbrancePenalty,
  1,
  95
)
```

Default `SequenceEdgeBonus = 0` unless granted by explicit feature.

## 4. Sequences & Advancement (Canonical Replacement)

## Advancement Gates

Every sequence advancement requires all three gates:

1. Narrative gate (milestone and acting/digestion completion)
2. Economy gate (ingredients/recipe or characteristic substitution)
3. Stability gate (not terminally corrupted)

## Advancement Resolution

Each advancement attempt always uses 3 stages:

1. Preparation (`Ritualism`)
2. Channeling (`Willpower` or `Endurance`, player choice)
3. Integration (`Ritualism`)

Per-stage modifier uses target tier:

- low `+0`
- mid `-5`
- high `-10`
- demigod `-15`
- angel `-20`
- god `-30`

### Stage Algorithm

```text
For each stage:
  Compute stage FinalTarget with universal check algorithm.
  Natural 1: stage success, +10 stage margin (does not count as extra stage)
  Natural 100: stage failure + immediate backlash check
  Otherwise: success/failure by Roll <= FinalTarget
```

Advancement succeeds on `2+` passed stages.

- `1` pass: failed ritual (no advancement)
- `0` pass: severe failed ritual

### Additional Prerequisite Ritual Requirement

When advancing into sequence `5` or lower (`6->5`, `5->4`, `4->3`, `3->2`, `2->1`, `1->0`):

- A prerequisite ritual framework must be completed with:
  - Anchor
  - Offering
  - Conduit
  - Price declaration
- Missing mandatory component applies `+10` complexity per missing component.

### Failure Consequences

- Failed ritual (1 pass): consume `50%` ingredients (round up), corruption `+8% MaxSanity`
- Severe failed ritual (0 pass): consume `100%` ingredients, corruption `+15% MaxSanity`
- Critical backlash: consume `100%` ingredients + 1 rare-equivalent, corruption `+25% MaxSanity`, trigger corruption event
- After failed attempt: no reattempt until one recovery arc is completed

## 6. Combat (Canonical Replacement)

## Action Economy

Per turn:

- `1 Action`
- `1 Move`
- `1 Reaction` per round

No universal Bonus Action. Bonus action exists only if explicitly granted by an ability.

## Movement & Threat

- Base speed: `30 ft`
- Threatened area: adjacent melee reach (`5 ft` unless modified)
- Leaving threatened area without `Disengage` triggers opportunity reaction
- Forced movement does not trigger opportunity reactions unless source says otherwise

## Standard Actions

- Attack
- Ability Use
- Dash/Position
- Guard
- Assist
- Disengage
- Use Item
- Stabilize

Guard and Assist are capped and non-stacking by source:

- Guard: `+5 DefenseShift` until start of your next turn
- Assist: `+5` to one declared check before start of your next turn
- A target cannot receive multiple Guard bonuses or multiple Assist bonuses from the same source category simultaneously

## Initiative Ordering

1. Successful initiative rollers act before failures.
2. Among successes: higher success margin acts first.
3. Among failures: lower failure margin acts first.
4. Ties: higher DEX, then higher LUCK, then reroll.

## Downed / Death Checks

```text
CorruptPenalty = min(6, floor(CurrentCorruptionPct / 10))
DeathCheckTarget = clamp(50 + floor(CON / 2) - CorruptPenalty, 1, 95)
```

At `3` death marks: death or irreversible corruption outcome (campaign option).

## 8. Rituals & Artifacts (Canonical Replacement)

## Ritual Types

- Advancement prerequisite rituals
- Invocation rituals
- Transit rituals

## Unified Ritual Check

```text
RitualTarget = clamp(
  35 + floor((WIL + INT + LUCK) / 3)
  + RitualProficiencyBonus
  - Complexity
  - CorruptionPenalty
  + CircleBonuses,
  1,
  95
)
```

Complexity references are authoritative in `core-tables-v1.csv`.

## Multi-Person Ritual Scaling

- Lead makes final ritual roll.
- Assist bonus:
  - first 2 successful assistants: `+5` each
  - next 2 successful assistants: `+3` each
  - additional successful assistants: `+1` each
  - max total assist: `+16`
- Instability:
  - assistant failure: `+1`
  - assistant critical failure: `+2`
  - at instability `3+`: `-10` to final roll and side effect even on success
  - at instability `5+`: automatic backlash event

## Artifact Strain & Corruption

Per activation:

```text
BaseStrain = 1 + Gap + AwakenedBonus + RepeatUseBonus
CorruptionGain = max(0, BaseStrain + ArtifactTaint - floor((WIL + CON + LUCK) / 45))
```

Where:

- `Gap = max(0, UserSequence - ArtifactSourceSequence)`
- `AwakenedBonus = 1` when awakened mode is used, else `0`
- `RepeatUseBonus = 1` when same artifact is used again in same scene after first activation, else `0`

Lifecycle clarifications:

- Scene strain resets to `0` after short rest.
- Persistent `ArtifactTaint` is reduced only by full purification ritual.
- Backlash checks are mandatory on critical failure or scene strain `5+`.

## Part V Reference Authority (Canonical Replacement)

All Part V benchmark and reference tables are sourced from:

- `core-tables-v1.csv` (authoritative balancing and progression data)
- `system-config-v1.json` (authoritative machine constants)

If text conflicts with those files, those files are authoritative for v1 implementation.
