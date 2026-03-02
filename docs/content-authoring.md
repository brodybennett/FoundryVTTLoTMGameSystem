# LoTM Content Authoring (Compendium-First)

This system uses JSON source files under `content-src/` as the editable source of truth.

## Required Entry Contract

Each content entry must include:

- `id` (stable, lowercase, regex `^[a-z][a-z0-9_.-]*$`)
- `pack` (target compendium pack name)
- `documentType` (`Item` or `RollTable`)
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

## Domains

- `content-src/pathways/`
- `content-src/abilities/`
- `content-src/items/`
- `content-src/rituals/`
- `content-src/artifacts/`
- `content-src/rolltables/`
- `content-src/configs/`

## Validation and Build

Run:

```bash
python scripts/validate_content_source.py
python scripts/build_compendiums.py
```

`validate_content_source.py` enforces:

- schema-like required fields
- ID and pack naming rules
- semver parse/order
- `minSystemVersion <= current system version`
- dependency existence (entry and system dependency blocks)
- global ID uniqueness
- vertical-slice minimum counts:
  - abilities >= 12
  - items >= 20
  - rituals >= 6
  - artifacts >= 4
  - roll tables >= 6
  - must include `pathway.seer`

`build_compendiums.py` generates deterministic `packs/*.db` using stable hashed `_id` values.

## Authoring Rules

- Never change existing IDs in published content.
- Increment `version` when semantics or balance change.
- Keep `minSystemVersion` realistic; do not set above current system version unless intentionally gating.
- Use `maxTestedSystemVersion` as a soft compatibility cap.
- Keep dependencies explicit so pack load order and migration are deterministic.