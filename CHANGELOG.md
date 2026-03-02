# Changelog

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