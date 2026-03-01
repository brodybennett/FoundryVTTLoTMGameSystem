# Rebalance Patch Spec v1.1 Hardening

## Objective
Define numeric guardrails that keep parity combat at 6-9 rounds while limiting apex runaway and preserving corruption pressure.

## 1) Success Curve Targets
- Trained non-combat checks (neutral conditions):
  - seq9: 40-50%
  - seq5: 50-60%
  - seq1: 58-68%
  - seq0: 62-75%
- Legendary checks should be +12 to +18 points above trained at equal sequence.

## 2) Durability and Resource Ratios
- Preserve TTK parity target: 6.0-7.2 rounds median for sequence mirrors.
- Spirit-to-HP midpoint ratio caps:
  - seq9-5: <=1.00
  - seq4-1: <=1.15
  - seq0: <=1.20

## 3) Corruption Pressure Bands
- 20-session benchmark (mixed-risk campaign profile):
  - Median final corruption: 45-60
  - Terminal outcomes: 3-8%
- Band trigger fidelity: mandatory events at 30/60/90/100 must always fire once per crossing.

## 4) Advancement Success Windows (Post-gate)
- low: 65-75%
- mid: 55-65%
- high: 40-55%
- demigod: 30-45%
- angel: 20-35%
- god: 10-25%

## 5) Artifact Risk/Reward Targets
- Equal-sequence normal activation expected net corruption: 1-3.
- Gap >=2, repeat-use, or awakened mode expected net corruption: 3-6.
- Scene-level backlash expectation above strain threshold should exceed 15%.

## 6) Fail-Fast Verification Gates
1. If any sequence mirror-combat median leaves 6-9 rounds, fail build.
2. If spirit/HP ratio exceeds sequence cap, fail build.
3. If corruption terminal rate leaves 3-8% band, fail build.
4. If advancement tier outcomes leave defined windows, fail build.
5. If any derived stat vector exits baseline min/max by sequence, fail build.
