# Changelog

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
