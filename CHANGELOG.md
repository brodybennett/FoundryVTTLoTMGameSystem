# Changelog

## 1.2.13

- Completed the sheet gold-standard program scope:
  - UX baseline rubric/checklist
  - character actor IA polish
  - actor workflow hardening
  - NPC divergence pass
  - item framework polish
  - subtype completion pass
- Added explicit sheet QA workflow references in core docs.
- Finalized full verification and release packaging for sheet-focused readiness.

## 1.2.12

- Completed subtype-specific item authoring UX across all registered item types.
- Added visibility gating so irrelevant identity/complexity controls are hidden by subtype.
- Added subtype guidance tips to improve consistency and reduce authoring ambiguity.
- Finalized item sheet labeling and spacing consistency pass.

## 1.2.11

- Reworked item sheet framework with clearer section hierarchy:
  - Overview
  - Subtype Data
  - Effects
  - Dependencies
- Added item subtype metadata context (labels/summaries) and inline validation issue display.
- Hardened effect row add/remove UX with safer IDs and explicit failure notifications.

## 1.2.10

- Added explicit NPC-focused sheet divergence while keeping a shared actor sheet base:
  - NPC-only snapshot section
  - NPC combat profile editing panel
  - consolidated NPC loadout view
  - NPC-specific quick-action roll button
- Reduced character-oriented clutter in NPC sheet flow.

## 1.2.9

- Hardened actor sheet actions to avoid silent failures:
  - explicit API availability checks
  - try/catch user notifications
  - numeric input guardrails for corruption delta
  - confirmation prompt for embedded item deletion
- Improved creation/finalize feedback messaging to produce deterministic blocker output.
- Added explicit empty-state messaging and interaction affordances across actor inventory/powers sections.

## 1.2.8

- Reworked character actor sheet information architecture with clearer panel hierarchy and consolidated quick actions.
- Improved tab naming and section framing for readability and workflow clarity.
- Improved actor sheet responsiveness for narrow widths and high-zoom layouts.

## 1.2.7

- Added sheet UX baseline documentation:
  - `docs/sheet-ux-rubric.md`
  - `docs/sheet-review-checklist.md`
- Introduced expanded sheet design tokens, layout utilities, and responsive behavior in `styles/lotm-system.css`.

## 1.2.6

- Fixed actor/item/compendium sheet opening failures by switching to system-qualified template paths.
- Added safe actor/item context fallback in sheet `getData()` for compatibility with open/render flows.

## 1.2.5

- Added version-consistency gate (`scripts/check_version_consistency.py`) and wired it into verification + release workflow preflight.
- Added GM-ready compendium folder organizer (`game.lotm.organizeCompendiums()`) with world setting `lotm-system.autoOrganizeCompendiums`.
- Hardened character creation with step validation/gating, guided pathway/sequence selectors, finalize blockers, and stronger repair behavior.
- Added subtype-aware item authoring sheet sections, CSV array editors, effects row scaffold, and runtime item create/update validation.
- Extended item schema/template contract with optional `system.pathwayData` and `system.sequenceData` authoring payload blocks.
- Expanded content authoring helper with typed scaffolds, pathway-bundle scaffolds, and metadata-only max-tested bulk bumping.

## 1.2.4

- Consolidated compendium packs for pathways, roll tables, items, and actors into unified top-level packs.
- Updated pathway import and rolltable resolution logic to work against unified compendiums.
- Updated manifest/build verification and authoring docs for the unified pack layout.
- Published version/tag alignment fix so release automation can generate Foundry update assets.

## 1.2.2

- Added strict roll-table source schema contract (`schemas/content.rolltable.schema.v1_2.json`).
- Enforced roll-table segment/formula/weight coherence and trigger-tag validation in content verifier.
- Added runtime roll-table APIs:
  - `game.lotm.rollOnSegment(segment, context={})`
  - `game.lotm.rollOnTableId(contentId, context={})`
- Wired automation hook routing for:
  - ritual failure -> `rituals`
  - artifact backlash -> `artifacts`
  - corruption threshold crossing -> `corruption`
- Added guided character creation wizard flow in actor sheet with step state tracking.
- Added actor ready validation and derived-stat finalization/repair utilities.
- Enforced ready-for-play gating for character roll automation when creation is incomplete.

## 1.2.1

- Reworked compendium architecture to target final browsing model:
  - per-pathway pathway packs
  - item packs by subtype
  - global abilities, rituals, and sealed artifacts packs
  - roll tables segmented by gameplay area
  - actor packs split by factions, beyonder monsters, and civilians
  - rules JournalEntry reference pack
- Added actor and rules source domains under `content-src/actors` and `content-src/rules`.
- Extended content validator and compendium builder for `Actor` and `JournalEntry` document generation.
- Added structured grouping metadata on generated documents for pathway/sequence/segment browsing.
- Updated manifest and verification checks to enforce the new pack layout.

## 1.2.0

- Added full Foundry runtime bootstrap with actor/item document classes, default sheets, and `game.lotm` API.
- Added roll automation primitives: `rollCheck`, `rollDamage`, `applyCorruption`, `rollRitualRisk`, `rollArtifactBacklash`.
- Added world migration gate and v1.2.0 migration backfills.
- Added Seer vertical-slice content source (`content-src/`) with pathway, abilities, items, rituals, artifacts, and roll tables.
- Added content validation and deterministic compendium build scripts generating `packs/*.db`.
- Added manifest `packs` declarations so compendiums ship and appear in Foundry sidebar.
- Expanded `template.json` and runtime templates for usable actor/item sheets and chat cards.

## 1.1.0

- Added initial FoundryVTT installable system package scaffold.
- Added GitHub Releases manifest and zip packaging pipeline.
