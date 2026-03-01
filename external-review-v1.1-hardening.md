## 1) Executive Verdict
- Overall readiness score (0-100): **74/100**
- Can this ship to Foundry prototype?: **Yes, conditionally.** Core math and schema foundations are now viable, but unresolved balancing definitions (especially corruption gain inputs and growth progression policy) still create high drift risk during content scaling.

## 2) Critical Issues (Top 15, highest severity first)
1. **Severity:** Blocker  
   **Rule section:** Ritual checks (`system-config-v1.1.json.formulaRegistry.check.ritual.v1`)  
   **Problem:** Ritual formula previously subtracted a negative `corruptionPenalty`, creating a success bonus under high corruption.  
   **Why it matters in play:** Corruption became an optimization vector instead of pressure.  
   **Why it matters for Foundry implementation:** Automation would enforce inverted risk and make rollback painful once content depends on it.  
   **Specific fix:** Use `+ corruptionPenalty` in ritual formula; lock this with verifier checks.

2. **Severity:** Blocker  
   **Rule section:** Condition effect paths vs Actor schema (`data/conditions.library.v1.1.json` vs `schemas/actor.system.schema.v1_1.json`)  
   **Problem:** Condition effects targeted `system.tracks.*` keys that were not defined in actor schema.  
   **Why it matters in play:** Condition behavior becomes inconsistent or silently fails.  
   **Why it matters for Foundry implementation:** Strict DataModel validation rejects undefined paths.  
   **Specific fix:** Add explicit `tracks` fields for all condition-targeted keys.

3. **Severity:** Blocker  
   **Rule section:** Manifest publish contract  
   **Problem:** Docs required unique IDs/paths and safe paths, but verifier did not enforce them.  
   **Why it matters in play:** Broken content packs can overwrite or shadow entries.  
   **Why it matters for Foundry implementation:** Import collisions and path traversal risks undermine pack integrity.  
   **Specific fix:** Enforce uniqueness and relative-safe paths in schema/validator.

4. **Severity:** High  
   **Rule section:** Item metadata policy  
   **Problem:** Dependencies were documented as required but not enforced by schema.  
   **Why it matters in play:** Content with unknown compatibility enters tables.  
   **Why it matters for Foundry implementation:** Version gating and migration warnings cannot be trusted.  
   **Specific fix:** Make `dependencies` required on all v1.1 items and validate fields.

5. **Severity:** High  
   **Rule section:** Formula extensibility  
   **Problem:** `formulaKey` used hardcoded enum values in schema.  
   **Why it matters in play:** New mechanical content needs core rewrites, slowing pathway expansion.  
   **Why it matters for Foundry implementation:** Violates compendium-first objective.  
   **Specific fix:** Change `formulaKey` to pattern and validate against runtime registry.

6. **Severity:** High  
   **Rule section:** Ability sequence gates  
   **Problem:** `minSequence <= sequence` coherence was not enforced.  
   **Why it matters in play:** Early unlocks and backward-gated exploits.  
   **Why it matters for Foundry implementation:** Automation cannot safely decide eligibility.  
   **Specific fix:** Add schema guardrails and semantic validator checks.

7. **Severity:** High  
   **Rule section:** Ability pathway permissions  
   **Problem:** `allowedPathwayIds` could exclude `pathwayId` with no rejection.  
   **Why it matters in play:** Content can self-contradict and produce hidden unusable abilities.  
   **Why it matters for Foundry implementation:** Eligibility checks branch unpredictably.  
   **Specific fix:** Semantic validation requiring `pathwayId` inclusion when allowlist exists.

8. **Severity:** High  
   **Rule section:** Effect lifecycle semantics  
   **Problem:** `saveType=none` effects still used `removeOn: saveSuccess`.  
   **Why it matters in play:** Removal conditions become impossible or GM-adjudicated ad hoc.  
   **Why it matters for Foundry implementation:** Deterministic effect engine cannot resolve dead triggers.  
   **Specific fix:** Forbid `saveSuccess` when `saveType=none`; clean condition data.

9. **Severity:** High  
   **Rule section:** Effect source categorization  
   **Problem:** Non-stacking-by-source is canonical, but `sourceCategory` was optional.  
   **Why it matters in play:** Stack behavior differs by GM interpretation.  
   **Why it matters for Foundry implementation:** Conflict resolution cannot be deterministic.  
   **Specific fix:** Make `sourceCategory` required on effects.

10. **Severity:** High  
    **Rule section:** Corruption gain model (`system-config-v1.1.json.corruption.gainFormula`)  
    **Problem:** `baseRisk`, `tierGapRisk`, `overdrawRisk` are referenced but not operationally defined.  
    **Why it matters in play:** Corruption pacing is table-dependent and abusable.  
    **Why it matters for Foundry implementation:** Cannot implement reproducible auto-gain logic.  
    **Specific fix:** Add explicit variable sources and bounds in config/tables.

11. **Severity:** Medium  
    **Rule section:** Growth model policy  
    **Problem:** `rateByTier` exists without sequence-step algorithm. Plausible multiplicative reading overshoots seq0 durability.  
    **Why it matters in play:** Tier 0 stat explosion distorts encounter math.  
    **Why it matters for Foundry implementation:** Auto-derived stats diverge from baseline tables.  
    **Specific fix:** Publish one canonical growth algorithm with test vectors.

12. **Severity:** Medium  
    **Rule section:** v1.1 prose completeness  
    **Problem:** v1.1 rulebook source omits some operational rules still present in v1 prose (contested/group specifics).  
    **Why it matters in play:** GMs fill gaps inconsistently.  
    **Why it matters for Foundry implementation:** Partial automation boundaries drift per table.  
    **Specific fix:** Promote required operational rules into v1.1 source or canonical appendices.

13. **Severity:** Medium  
    **Rule section:** Verification scope split  
    **Problem:** Phase 1 verification remains anchored to v1 files while v1.1 evolves.  
    **Why it matters in play:** Regression confidence is overstated.  
    **Why it matters for Foundry implementation:** Pipeline can pass while v1.1 semantics regress.  
    **Specific fix:** Add v1.1 semantic checks in Phase 2 (now added) and keep them in release gate.

14. **Severity:** Medium  
    **Rule section:** Simulation representativeness  
    **Problem:** Current parity sims are symmetric DPR-vs-HP loops without control/status/action-economy asymmetry.  
    **Why it matters in play:** Balance appears stable until real status-heavy fights.  
    **Why it matters for Foundry implementation:** Automated balance tuning uses weak signal.  
    **Specific fix:** Add scenario sims with conditions, reactions, and resource starvation.

15. **Severity:** Low  
    **Rule section:** Effect path governance  
    **Problem:** Prefix whitelist is broad and allows semantically invalid paths inside approved prefixes.  
    **Why it matters in play:** Hidden no-op or broken effects leak into packs.  
    **Why it matters for Foundry implementation:** Runtime errors become content-authoring bugs.  
    **Specific fix:** Add schema-derived path allowlist generation for high-risk fields.

## 3) Balance Audit
- **Attribute growth and modifier scaling:** Skill target scaling is flat-to-moderate under base formula, but growth policy remains underspecified. Under one plausible multiplicative interpretation from `anchorMin=10` and `rateByTier`, seq0 attributes reach ~55.7 and can generate HP ~1069 (above baseline max 800). This is a structural risk.
- **DPR/HP/Spirit curves by tier:** Baseline midpoints produce estimated TTK ~6.1-6.8 rounds across seq9->0, which matches profile goals. Spirit/HP ratio climbs from ~0.92 (seq9) to ~1.26 (seq0), indicating caster stamina dominance at apex.
- **Action economy:** 1 Action / 1 Move / 1 Reaction is stable and exploitable only through unchecked extra-action effects (none currently universal).
- **Corruption pressure and failure bands:** Campaign sim currently yields median final corruption ~55 and terminal ~7.82% over 20 sessions. Pressure exists, but unresolved gain variable definitions can swing this sharply.
- **Advancement pacing and economy gates:** If stage success rates follow tier bands (70/60/50/40/30), 3-stage 2-pass success probabilities are ~78.4% / 64.8% / 50% / 35.2% / 21.6% before narrative/economy gate friction.
- **Ritual and artifact risk/reward:** Ritual now correctly penalized by corruption term. Artifact strain model remains in older prose and should be promoted into v1.1 canonical source to avoid drift.

**Concrete rebalance targets**
- Trained non-combat skill success target bands (no situational mods):
  - seq9: 40-50%
  - seq5: 50-60%
  - seq1: 58-68%
  - seq0: 62-75%
- Spirit/HP midpoint ratio cap: keep <=1.15 through seq1 and <=1.20 at seq0.
- Corruption campaign outcomes (20-session benchmark): median final 45-60, terminal 3-8%.
- Advancement success (post-gate, per attempt):
  - low 65-75%, mid 55-65%, high 40-55%, demigod 30-45%, angel 20-35%, god 10-25%.
- Artifact expected net corruption gain per activation:
  - equal-sequence normal mode: 1-3
  - gap >=2 or repeat-use scene stacking: 3-6

## 4) FoundryVTT Implementation Audit
- **Data model/schema completeness:** Improved materially with track-field alignment and effect/item hardening. Remaining gap is explicit corruption gain variable sources.
- **Automated vs manual boundary:**
  - Auto: check math, target clamp, resource spend, cooldown/usage limits, effect lifecycle, corruption bands, manifest/schema validation.
  - Semi-auto: advancement flow UI with GM gate toggles, ritual complications, backlash prompts.
  - Manual: narrative gates, story consequences, major corruption event fiction.
- **Roll formula standardization:** Use formula registry keys and resolve to deterministic roll packets:
  - `{ formulaKey, baseTarget, modifiers[], penalties[], finalTarget, roll, margin, criticalFlag, context }`
- **Compendium structure/extensibility:** Registry-driven formula keys and semantic validators now support no-code additions for most new content types.
- **Import/export/versioning/migration risks:** v1 coexistence is intact, but semantic drift between v1 and v1.1 must be guarded by phase2 semantic gates in CI.

**Recommended Foundry-ready schema outline**
- `Actor.system`: identity, attributes, skills, derived, resources, progression, tracks, ritual, artifacts, version.
- `Item.system`: core metadata, activation/resource/cost/cooldown, sequence/pathway gating, formula key, effects, dependencies, usage constraints.
- `Effect`: operation + lifecycle + source category + save semantics + stack controls.
- `Manifest`: pack metadata + unique entry map + safe relative paths.

## 5) Extensibility Audit (Compendium-first design)
- **Readiness verdict:** **Partially ready, now close to target.**
- New pathways/abilities/items/rituals/artifacts can be added without core code changes when they stay inside schema + registry + semantic validator gates.
- Required governance/validation rules:
  - Immutable IDs.
  - Mandatory dependency metadata.
  - Runtime formula registry validation.
  - Pathway and sequence coherence checks.
  - Effect lifecycle compatibility checks.
  - Manifest uniqueness and path safety.
  - Source-category discipline for stacking resolution.

## 6) Ambiguities & Missing Rules
1. Operational definitions for `baseRisk`, `tierGapRisk`, `overdrawRisk` in corruption gain.
2. Canonical sequence-step attribute growth algorithm (not just tier rates).
3. v1.1 authoritative artifact strain text (currently scattered in older prose).
4. Reattempt cooldown semantics after failed advancement (`recovery arc`) in machine-readable form.
5. Whether passive/contested/group check tie-breakers remain fully canonical in v1.1 runtime.
6. Explicit handling policy for dual-pathway content remains assumption-only in decision logs.

## 7) Exploit / Abuse Cases
1. **Corruption-positive ritual loop** (closed): fixed ritual penalty sign.
2. **Early unlock ability payloads:** `minSequence > sequence` now rejected.
3. **Pathway spoofing payloads:** allowlist mismatch now rejected by semantic validator.
4. **No-save infinite condition hooks:** `saveSuccess` with `saveType=none` now forbidden.
5. **Pack collision injection:** duplicate IDs/paths now rejected.
6. **Manifest traversal abuse:** relative safe-path validation now enforced.
7. **Source-less stacking abuse:** `sourceCategory` now required.
8. **Future formula injection bypass:** unknown `formulaKey` now rejected via registry check.

## 8) Rewrite Proposals
1. **Ritual Corruption Term**
```text
RitualTarget = clamp(
  35 + floor((WIL + INT + LUCK) / 3) + RitualProficiency - Complexity + CorruptionPenalty + CircleBonuses,
  1,
  95
)
```

2. **Ability Sequence and Pathway Eligibility**
```text
An ability is valid only when all are true:
1) actor.sequence <= ability.minSequence
2) ability.minSequence <= ability.sequence
3) if allowedPathwayIds exists, it contains ability.pathwayId
```

3. **Effect Save Compatibility**
```text
If saveType = none, set saveTarget = 0 and do not include removeOn: saveSuccess.
If saveType != none, saveTarget must be 1..95.
```

4. **Cost Operation Safety**
```text
For effects with op = cost, value must be non-negative.
```

5. **Manifest Safety Rule**
```text
Each manifest entry id and path must be unique within the pack.
Entry paths must be relative and cannot include '..'.
```

## 9) Test Matrix
- **Unit**
  - `ability.minSequence <= sequence` invariant checks.
  - `allowedPathwayIds` includes `pathwayId` when both are present.
  - Effect matrix: (`saveType`, `saveTarget`, `removeOn`) compatibility.
  - Manifest uniqueness and safe-path checks.
- **Simulation**
  - 10k parity combats per sequence with status/control variants.
  - Ritual pass-rate by tier under corruption bands 0/30/60/90.
  - Corruption campaign profiles for low/medium/high-risk usage.
- **Playtest**
  - Parity fights at seq9/6/3/1/0.
  - Artifact repeat-use and backlash pressure scenarios.
  - Corruption brink play at 60% and 90% thresholds.
  - Advancement attempts at 6->5, 3->2, 1->0.
- **Pipeline**
  - v1 import into v1.1 migration path.
  - v1.1 optional field presence/absence permutations.
  - Duplicate manifest IDs/paths rejected.
  - Roundtrip docx canonical marker checks.

## 10) Prioritized Roadmap
- **Phase 1 = must-fix blockers**
  - Ritual corruption sign lock.
  - Actor tracks/schema-condition alignment.
  - Manifest uniqueness/path safety enforcement.
  - Item/effect semantic hardening (`dependencies`, sequence/pathway checks, save/cost/source rules).
- **Phase 2 = high-value improvements**
  - Formalize corruption gain variable definitions in config/tables.
  - Publish canonical growth algorithm and vector tests.
  - Extend simulation harness to include status/control asymmetry.
- **Phase 3 = polish**
  - Expand author-facing linting diagnostics.
  - Add schema-derived path allowlist generation.
  - Promote artifact and contested/group operational text into v1.1 canonical source.

**Assumptions**
- Authoritative scope is v1.1 stack in repo.
- Balance priority is anti-exploit stability over maximal fantasy spikes.
- Hybrid automation boundary remains.
- Backward compatibility target remains v1 -> v1.1 additive.
- This review intentionally prioritizes implementation certainty over flavor prose.
