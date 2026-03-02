# Changelog

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