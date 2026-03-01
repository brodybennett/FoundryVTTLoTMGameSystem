# Phase 1 Test Matrix v1.1

## Blocker Regression Tests

1. Universal clamp lock
- Verify all canonical core checks clamp target to `1..95`.

2. Action economy lock
- Verify no universal bonus action appears in canonical source.
- Verify combat turn budget remains `1 Action, 1 Move, 1 Reaction`.

3. Skill formula lock
- Verify canonical source uses only:
  `25 + floor(LinkedAttribute / 3) + ProficiencyBonus + floor(LUCK / 10)`.

4. Corruption lock
- Verify penalty progression is `-1 per 10%`, cap `-6`.

5. Ability schema lock
- Verify canonical ability example uses flat item schema contract fields.

6. Ritual sign lock
- Verify ritual check text applies `+ CorruptionPenalty` and never subtracts it.

7. Ability semantics lock
- Verify canonical source states `ability.minSequence <= ability.sequence`.

8. Effect lifecycle lock
- Verify canonical source requires `sourceCategory`.

## Contract Audit Tests

1. Required canonical text presence check.
2. Banned pattern rejection:
- `1 Bonus Action` as universal rule.
- `clamp(..., 1, 100)` in core check formulas.
- alternate sheet skill formula (`30 + floor(Linked Attribute / 2)`).
- corruption penalties below `-6`.
- ritual formula using `- CorruptionPenalty`.

## Acceptance Criteria

1. `python scripts/rulebook_contract_audit.py --rulebook rulebook-source-v1.1.md` passes.
2. `python scripts/phase1_verification.py` passes with integrated contract audit.
