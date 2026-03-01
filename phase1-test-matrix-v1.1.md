# Phase 1 Test Matrix v1.1

## Blocker Regression Tests

1. Universal clamp lock
- Verify all canonical core checks clamp target to `1..95`.

2. Combat pipeline lock
- Verify canonical source defines attack target formula and damage resolution order.
- Verify critical behavior:
  - natural 1 doubles base damage
  - natural 100 auto-miss

3. Action economy lock
- Verify no universal bonus action appears in canonical source.
- Verify combat turn budget remains `1 Action, 1 Move, 1 Reaction`.

4. Skill formula lock
- Verify canonical source uses only:
  `25 + floor(LinkedAttribute / 3) + ProficiencyBonus + floor(LUCK / 10)`.

5. Corruption lock
- Verify penalty band progression:
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
- Verify corruption is tracked as flat points on `0..100`.

6. Downed/death lock
- Verify canonical source defines:
  - `check.death.v1`
  - 3 marks = death
  - 3 saves = stabilize
  - damage while downed adds mark
  - healing above 0 HP resets counters

7. Advancement lock
- Verify channeling defaults to `willpower` and allows pre-roll declared `endurance`.
- Verify advancement failure penalties use flat corruption gain fields.

8. Ability schema lock
- Verify canonical ability example uses flat item schema contract fields.

9. Ritual scaling/sign lock
- Verify ritual check text uses `floor((WIL + INT + LUCK) / 9)`.
- Verify ritual check text applies `+ CorruptionPenalty` and never subtracts it.

10. Ability semantics lock
- Verify canonical source states `ability.minSequence <= ability.sequence`.

11. Effect lifecycle lock
- Verify canonical source requires `sourceCategory`, `target`, and `trigger`.

## Contract Audit Tests

1. Required canonical text presence check.
2. Banned pattern rejection:
- `1 Bonus Action` as universal rule.
- `clamp(..., 1, 100)` in core check formulas.
- alternate sheet skill formula (`30 + floor(Linked Attribute / 2)`).
- corruption penalties below `-10`.
- ritual formula using `- CorruptionPenalty`.
- ritual formula using `/3` attribute divisor.
- advancement penalties expressed as `% of max sanity`.

## Acceptance Criteria

1. `python scripts/rulebook_contract_audit.py --rulebook rulebook-source-v1.1.md` passes.
2. `python scripts/phase1_verification.py` passes with integrated contract audit.
