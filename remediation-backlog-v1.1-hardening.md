# Remediation Backlog v1.1 Hardening

## Scope
Blocker-first implementation backlog derived from `external-review-v1.1-hardening.md`, with explicit file-level assignments and test acceptance criteria.

## Phase 1 Blockers (Must Ship)

### BLK-01 Ritual Corruption Penalty Sign Lock
- Goal: Ensure corruption can never improve ritual success.
- Files:
  - `system-config-v1.1.json`
  - `scripts/phase2_verification.py`
- Changes:
  - Set ritual formula corruption term to `+ corruptionPenalty`.
  - Add verifier assertion rejecting `- corruptionPenalty` form.
- Acceptance:
  - `python scripts/phase2_verification.py` passes.
  - Ritual formula string contains `+ corruptionPenalty`.

### BLK-02 Actor Tracks / Condition Path Contract Alignment
- Goal: Ensure every `system.tracks.*` condition mutation targets schema-defined fields.
- Files:
  - `schemas/actor.system.schema.v1_1.json`
  - `data/conditions.library.v1.1.json`
  - `scripts/phase2_verification.py`
- Changes:
  - Add explicit tracks fields for action lock, movement penalty, offense/defense modifiers, verbal lock, downed state.
  - Remove invalid `saveSuccess` removals from no-save condition entries.
  - Add verifier check mapping condition paths to actor schema keys.
- Acceptance:
  - Conditions library semantic check passes.
  - No undefined `system.tracks.*` targets remain.

### BLK-03 Manifest Collision and Path Safety Gate
- Goal: Block duplicate IDs/paths and unsafe entry paths at publish time.
- Files:
  - `schemas/content.pack.manifest.schema.v1_1.json`
  - `scripts/phase2_verification.py`
  - `content-validation-rules-v1.1.md`
- Changes:
  - Add path safety regex in schema.
  - Enforce duplicate ID/path rejection in verifier.
  - Document unique/path-safe publish rules.
- Acceptance:
  - Synthetic tests reject duplicate ID/path and `../` path.

### BLK-04 Item Semantic Hardening
- Goal: Prevent sequence/pathway/compatibility exploit payloads.
- Files:
  - `schemas/item.system.schema.v1_1.json`
  - `scripts/phase2_verification.py`
  - `content-validation-rules-v1.1.md`
  - `authoring-cookbook-v1.1.md`
- Changes:
  - Require `dependencies` on all items.
  - Enforce `minSequence <= sequence` semantics.
  - Enforce `allowedPathwayIds` contains `pathwayId` when both exist.
  - Move `formulaKey` from enum-lock to registry-driven validation.
- Acceptance:
  - Negative vectors fail for each semantic rule.
  - Positive vector passes all checks.

### BLK-05 Effect Semantic Hardening
- Goal: Make lifecycle deterministic and stack-safe.
- Files:
  - `schemas/effect.schema.v1_1.json`
  - `scripts/phase2_verification.py`
  - `content-validation-rules-v1.1.md`
- Changes:
  - Require `sourceCategory`.
  - Enforce save-target compatibility by saveType.
  - Forbid `removeOn: saveSuccess` when `saveType = none`.
  - Require non-negative cost value for `op = cost`.
- Acceptance:
  - All conditions/effects satisfy new semantics.

## Phase 2 High-Value Improvements

### HV-01 Corruption Gain Variable Formalization
- Files:
  - `system-config-v1.1.json`
  - `core-tables-v1.csv`
  - `rules-canon-v1.1.md`
- Change:
  - Define canonical variable sources/ranges for `baseRisk`, `tierGapRisk`, `overdrawRisk`.
- Acceptance:
  - Deterministic corruption-gain examples exist for at least 10 vectors.

### HV-02 Growth Algorithm Canonicalization
- Files:
  - `system-config-v1.1.json`
  - `core-tables-v1.csv`
  - `phase1-test-matrix-v1.1.md`
- Change:
  - Publish exact sequence-step growth algorithm and expected derived stat vectors.
- Acceptance:
  - Derived HP/Spirit/Sanity vectors remain inside baseline windows for each sequence.

### HV-03 Simulation Realism Upgrade
- Files:
  - `scripts/phase1_verification.py`
  - `phase1-test-matrix-v1.1.md`
- Change:
  - Add condition/control/resource asymmetry scenarios.
- Acceptance:
  - New simulations run in CI under existing deterministic seed policy.

## Phase 3 Polish

### POL-01 Path Allowlist Generator
- Files:
  - `scripts/*` (new utility)
  - `system-config-v1.1.json`
- Change:
  - Generate field-level safe mutation paths from schemas.
- Acceptance:
  - Generated allowlist diff is reproducible.

### POL-02 v1.1 Canon Text Completeness Lift
- Files:
  - `rulebook-source-v1.1.md`
  - `rules-canon-v1.1.md`
- Change:
  - Pull contested/group/artifact operational details into v1.1 source.
- Acceptance:
  - Prose contains all runtime-critical mechanics currently implied elsewhere.

### POL-03 Author-Facing Lint Diagnostics
- Files:
  - `scripts/phase2_verification.py`
  - `authoring-cookbook-v1.1.md`
- Change:
  - Emit per-entry actionable lint messages.
- Acceptance:
  - Every reject has deterministic code + human-readable remediation.
