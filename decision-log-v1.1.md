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

7. Corruption penalty remains capped at `-6`.

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

## Assumptions

- Dual-pathway remains disabled by default.
- Narrative gates remain GM authority under hybrid automation.
- No backward compatibility required for pre-v1 draft objects.
