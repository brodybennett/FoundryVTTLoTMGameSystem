# LoTM Canon v1 Decision Log

Date: 2026-03-01

## Locked Decisions

1. Universal target clamp uses `1..95` for all core checks.
- Rationale: prevent auto-success saturation at high tiers.

2. Skill formula unified to:
- `25 + floor(LinkedAttribute / 3) + ProficiencyBonus + floor(LUCK / 10)`
- Rationale: remove contradictions and tame runaway reliability.

3. Proficiency scale locked:
- `0 / 5 / 10 / 15 / 20 / 25`
- Rationale: bounded growth, still meaningful specialization.

4. Recovery fixed:
- short rest `0.45`, long rest full unless blocked.
- Rationale: correct typo-level blocker and preserve attrition gameplay.

5. Corruption penalties unified:
- `-1 per 10%`, capped at `-6`, trigger events at `30/60/90/100`.
- Rationale: deterministic pressure without binary shutdown.

6. Sequence/tier map locked:
- `9-8 low`, `7-6 mid`, `5 high`, `4-2 demigod`, `1 angel`, `0 god`.
- Rationale: remove mapping ambiguity for formulas and content gating.

7. Advancement rules unified:
- Always 3 stages; pass on 2+; natural `1` adds margin only; natural `100` stage fail + backlash.
- Rationale: closes critical ambiguity and exploit path.

8. Additional prerequisite ritual gate:
- Required when advancing into sequence `5` or lower.
- Rationale: preserve LoTM thematic escalation and risk.

9. Combat action economy locked:
- `1 Action`, `1 Move`, `1 Reaction`; no universal bonus action.
- Rationale: reduce baseline complexity and action inflation.

10. Guard/Assist reduced to `+5`, non-stacking by source.
- Rationale: close stacking abuse and defense inflation.

11. Movement baseline locked:
- base speed `30 ft`, threatened melee range `5 ft`.
- Rationale: remove tactical ambiguity and enable automation hooks.

12. Schema-first compendium governance added.
- Rationale: allow content expansion without core rewrites.

## Assumptions Kept

- Currency remains `cp`.
- Dual-pathway remains disabled by default.
- Narrative gate adjudication remains GM authority.
- No backward compatibility required with pre-v1 draft data.
