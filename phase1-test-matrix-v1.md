# Phase 1 Test Matrix v1

## Unit Tests

1. Formula consistency across sheet/chat/macro
- Given identical inputs, all three paths return the same target, result, margin, and critical flag.
- Pass if values are identical for at least 100 deterministic vectors.

2. Recovery correctness
- Short rest equals `round(max * 0.45)`.
- Recovery cannot exceed max.
- Pass if all vectors satisfy both.

3. Corruption penalty boundaries
- Penalty changes only at full 10% bands.
- Penalty cap is `-6`.
- Pass boundary vectors: `0,9,10,19,...,100`.

4. Advancement determinism
- Same stage inputs always produce the same outcome.
- Natural `1` grants margin bonus only (no extra stage success).
- Natural `100` auto-fails stage and sets backlash flag.
- Pass if deterministic and rule-conformant.

5. Condition lifecycle order
- Apply/tick/remove phases resolve in deterministic order.
- Pass if start/end turn processing is stable across repeated runs.

## Simulation Tests

1. Combat parity simulation
- 10k sequence-parity combats per sequence.
- Median rounds to resolution must be `6-9`.
- Pass per sequence and global aggregate.

2. Ritual success simulation
- 10k ritual checks per target tier.
- Success rates must stay within configured target bands:
  - mid: 65-75
  - high: 55-65
  - demigod: 45-55
  - angel: 35-45
  - god: 25-35

3. Corruption campaign simulation
- Simulate 20 sessions with repeated risky actions and recovery.
- Pass if corruption is non-zero pressure but avoids automatic death spiral:
  - median final corruption between 20 and 70
  - terminal outcomes are >0% and <10%

## Content Validation Tests

1. Invalid enum rejection
- Import entry with bad enum value.
- Must fail validation.

2. Missing `formulaKey` rejection
- Ability without `formulaKey` must fail validation.

3. Dependency rejection
- Entry referencing unknown required ID must fail validation.

4. Schema migration compatibility
- v1 baseline object upgraded to v1+1 mock migration path.
- Pass if required fields preserved and no invalid states introduced.
