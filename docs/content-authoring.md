# LoTM Content Authoring (Compendium-First)

This system uses JSON source files under `content-src/` as the editable source of truth.

## Required Entry Contract

Each content entry must include:

- `id` (stable, lowercase, regex `^[a-z][a-z0-9_.-]*$`)
- `pack` (source grouping key; final output pack can be routed by builder)
- `documentType` (`Item`, `RollTable`, `Actor`, or `JournalEntry`)
- `name`
- `version` (semver `X.Y.Z`)
- `minSystemVersion` (semver)
- `maxTestedSystemVersion` (semver)
- `dependencies` (array of content IDs)

### For `Item` entries

Required additional fields:

- `itemType`
- `system` object
- `system.id` must equal entry `id`
- `system.dependencies` with:
  - `minSystemVersion`
  - `maxTestedSystemVersion`
  - optional `requiresIds`
- optional `system.pathwayData` object
- optional `system.sequenceData` object

### For `RollTable` entries

Required additional fields:

- must satisfy `schemas/content.rolltable.schema.v1_2.json`
- `segment` (required enum): `resources`, `abilities`, `rituals`, `artifacts`, `corruption`, `encounters`
- `formula` (required): `1dN`
- `results` array
- each result requires `text` and `weight` (integer >= 1)
- weighted sum of results must match `N` from `formula`
- optional `triggerTags[]` (for runtime automation traceability)

### For `Actor` entries

Required additional fields:

- `actorType` (`character` or `npc`)
- `system` object

### For `JournalEntry` entries

Required additional fields:

- `pages` array
- each page requires:
  - `title`
  - `content`
  - optional `format` (`0` or `1`)

## Domains

- `content-src/pathways/`
- `content-src/abilities/`
- `content-src/items/`
- `content-src/rituals/`
- `content-src/artifacts/`
- `content-src/rolltables/`
- `content-src/actors/`
- `content-src/rules/`
- `content-src/configs/`

## Build Routing Model

`build_compendiums.py` routes source entries into final compendium packs:

- `pathway` / `sequenceNode` -> `pathways`
- `ability` -> `abilities`
- `ritual` -> `rituals`
- `artifact` -> `sealed-artifacts`
- all other item subtypes -> `items`
- roll tables -> `rolltables` (segment retained in `flags.lotm.groups.segment`)
- actors -> `actors` (source category retained in `flags.lotm.groups.category`)
- journals -> source `pack` value (rules reference)

At runtime, GM users get automatic native compendium folder organization (idempotent), controlled by world setting `lotm-system.autoOrganizeCompendiums` and manually callable with `game.lotm.organizeCompendiums()`.

Folder groups:

- pathways: folder per pathway (`flags.lotm.groups.pathwayId`)
- rolltables: folder per segment (`flags.lotm.groups.segment`)
- items: folder per item type group
- actors: folder per category (`flags.lotm.groups.category`)

## Validation and Build

Run:

```bash
python scripts/check_version_consistency.py
python scripts/validate_content_source.py
python scripts/build_compendiums.py
```

`validate_content_source.py` enforces:

- required fields by document type
- ID and pack naming rules
- semver parse/order
- `minSystemVersion <= current system version`
- dependency existence (entry and item dependency blocks)
- global ID uniqueness
- vertical-slice minimum counts:
  - abilities >= 12
  - item bucket entries >= 20
  - rituals >= 6
  - artifacts >= 4
  - roll tables >= 6
  - must include `pathway.seer`
- actor category presence:
  - `actors-factions`
  - `actors-beyonder-monsters`
  - `actors-civilians`
- rules pack presence:
  - `rules-reference`

`build_compendiums.py` generates deterministic `packs/*.db` using stable hashed `_id` values.

## Content Tool Scaffolding

Generate typed skeleton entries:

```bash
python scripts/content_tool.py new --type ability --id ability.example.new --name "New Ability"
python scripts/content_tool.py new --type weapon --id item.example.weapon --name "Example Weapon"
python scripts/content_tool.py new-pathway-bundle --pathway-id pathway.example --pathway-name Example --top-sequence 9 --bottom-sequence 7
```

Metadata-only compatibility bump flow (no gameplay/content semantics change):

```bash
python scripts/content_tool.py bump-max-tested --version 1.2.5
python scripts/content_tool.py bump-max-tested --version 1.2.5 --write
```

## Authoring Rules

- Never change existing IDs in published content.
- Increment `version` when semantics or balance change.
- Keep `minSystemVersion` realistic; do not set above current system version unless intentionally gating.
- Use `maxTestedSystemVersion` as a soft compatibility cap.
- Keep dependencies explicit so pack load order and migration are deterministic.
