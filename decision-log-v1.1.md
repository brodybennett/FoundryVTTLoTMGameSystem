# LoTM Canon v1.1 Decision Log

Date: 2026-03-01

## Locked Decisions

1. Markdown-first source of truth:
- `rulebook-source-v1.1.md` is editable source.
- `.docx` is generated publish artifact.

2. Canonical precedence is explicit:
- machine-readable config/tables/schemas override prose conflicts.

3. v1.1 versioning is additive:
- v1 files remain valid and frozen baseline.
- v1.1 introduces optional fields and new validation contracts.

4. Universal check clamp remains `1..95`.

5. No universal bonus action is allowed.

6. Skill formula remains:
- `25 + floor(attr/3) + proficiency + floor(luck/10)`.

7. Corruption penalty uses locked band-table escalation to `-10`:
- `0-9: 0`
- `10-19: -1`
- `20-29: -2`
- `30-39: -3`
- `40-49: -4`
- `50-59: -5`
- `60-69: -6`
- `70-79: -7`
- `80-89: -8`
- `90-100: -10`

8. Ability data contract must align with item schema:
- no nested divergent `usage` block in canonical examples.

9. Skill IDs become registry-backed in v1.1.

10. Condition templates become machine-defined library entries in v1.1.

11. Compendium publish requires pack manifest validation in v1.1.

12. Verification pipeline is mandatory:
- Phase 1 checks
- Phase 2 checks
- rulebook contract audit
- docx roundtrip audit

13. Ritual formula hardening:
- `check.ritual.v1` uses `+ corruptionPenalty` to prevent sign inversion.

14. v1.1 semantic validation hardening:
- manifest uniqueness/path safety is enforced.
- item ability semantics (`minSequence <= sequence`, pathway allowlist coherence) are enforced.
- effect lifecycle compatibility and non-negative `cost` operations are enforced.

15. Source-category stack resolution is runtime-required:
- `sourceCategory` is required for v1.1 effects.

16. Combat pipeline is now explicit:
- attack target formula and damage order are canonicalized in prose/config.

17. Downed/death track is now explicit:
- `deathMarks` and `deathSaves` are both canonical resources.
- 3 marks = death, 3 saves = stabilize.

18. Advancement channeling and failure units are fixed:
- channeling defaults to `willpower`, with declared `endurance` alternative.
- failure penalties use flat corruption points, not `% of max sanity`.

19. Ritual scaling is corrected:
- ritual attribute contribution uses `floor((WIL + INT + LUCK) / 9)`.

20. Typed item contracts and effect target/trigger are required:
- type payload blocks are mandatory by item type.
- effect `target` and `trigger` are required fields.

21. Phase 2 balance calibration and extensibility hardening:
- derived HP/Spirit calibration checks run against baseline midpoint bands with gate mode support.
- validation gate mode defaults to `warn` and may be promoted to strict later.
- registry validation is open-extension with canonical required subset.
- semver ordering and dependency graph checks are enforced for publish safety.

## Assumptions

- Dual-pathway remains disabled by default.
- Narrative gates remain GM authority under hybrid automation.
- No backward compatibility required for pre-v1 draft objects.
