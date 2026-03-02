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

### For `RollTable` entries

Required additional fields:

- `results` array
- each result requires `text`, optional `weight` (integer >= 1)
- optional `formula` (defaults to weighted `1dN` range)
- optional `segment` (`resources`, `abilities`, `rituals`, `artifacts`, `corruption`, `encounters`, etc.)

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

- `pathway` / `sequenceNode` -> `pathways-<pathway>`
- `ability` -> `abilities`
- `ritual` -> `rituals`
- `artifact` -> `sealed-artifacts`
- `weapon` -> `items-weapons`
- `armor` -> `items-armor`
- `consumable` -> `items-consumables`
- `ingredient` -> `items-ingredients`
- other item subtypes -> `items-gear`
- roll tables -> `rolltables-<segment>`
- actors -> source `pack` value (e.g., faction/monster/civilian)
- journals -> source `pack` value (rules reference)

## Validation and Build

Run:

```bash
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

## Authoring Rules

- Never change existing IDs in published content.
- Increment `version` when semantics or balance change.
- Keep `minSystemVersion` realistic; do not set above current system version unless intentionally gating.
- Use `maxTestedSystemVersion` as a soft compatibility cap.
- Keep dependencies explicit so pack load order and migration are deterministic.