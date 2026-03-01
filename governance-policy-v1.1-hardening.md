# Content Governance Policy v1.1 Hardening

## Purpose
Prevent broken or exploitative compendium content from shipping without core code changes.

## 1) ID and Version Governance
- IDs are immutable and must match `^[a-z][a-z0-9_.-]*$`.
- Every item must include:
  - `dependencies.minSystemVersion`
  - `dependencies.maxTestedSystemVersion`
- Major version mismatch: reject.

## 2) Formula Registry Governance
- `formulaKey` must resolve through `system-config-v1.1.json.formulaRegistry`.
- New formulas are added by config update and test-vector expansion; schema enum edits are prohibited.

## 3) Sequence and Pathway Governance
- For abilities, `minSequence <= sequence` is mandatory.
- If `allowedPathwayIds` exists, it must include `pathwayId`.
- Cross-pathway access must be explicit in content, never inferred.

## 4) Effect Governance
- `sourceCategory` is mandatory.
- Save compatibility:
  - `saveType = none` -> `saveTarget = 0` and no `removeOn: saveSuccess`
  - `saveType != none` -> `saveTarget in 1..95`
- `op = cost` requires non-negative value.
- Effects may only mutate whitelisted `system.*` path prefixes.

## 5) Manifest Governance
- Entry IDs must be unique within pack.
- Entry paths must be unique within pack.
- Entry paths must be relative and cannot contain `..`.

## 6) Publish Gate Governance
A pack is publishable only when all pass:
1. Schema validation.
2. Semantic validation (item/effect rules).
3. Registry checks (skills/conditions/formulas).
4. Manifest uniqueness/path safety checks.
5. Verification scripts (Phase 1 and Phase 2).

## 7) Exception Policy
- No production exceptions for blockers.
- Temporary dev-mode warnings are allowed only for non-balance metadata style issues.
- Any exception requires explicit expiry and owner in release notes.
