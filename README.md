# LoTM Game System for Foundry VTT

FoundryVTT game system package for a Lord of the Mysteries-inspired TTRPG.

## Install in Foundry

In Foundry VTT:

1. Open `Game Systems`.
2. Click `Install System`.
3. Paste this Manifest URL:

`https://github.com/brodybennett/FoundryVTTLoTMGameSystem/releases/latest/download/system.json`

## Compendium Structure (v1.2.1)

The system publishes compendiums in this access layout:

- `Pathways: <PathwayName>` packs (example: `Pathways: Seer` with pathway and sequence nodes)
- `Items` split by subtype:
  - `Items: Weapons`
  - `Items: Armor`
  - `Items: Gear and Features`
  - `Items: Consumables`
  - `Items: Ingredients`
- `Sealed Artifacts` (cross-pathway, grouped by sequence in naming/flags)
- `Abilities (All Pathways)` (grouped by pathway + sequence in naming/flags)
- `Rituals (All Pathways)` (pathway/universal grouping supported)
- `Roll Tables` segmented by gameplay area:
  - Resources, Abilities, Rituals, Artifacts, Corruption, Encounters
- `Actors` grouped by category:
  - Faction NPCs
  - Beyonder Monsters
  - Civilians
- `Rules: Hyperlinked Reference` (JournalEntry rules compendium with table-of-contents links)

## Create a Playable World

1. Create a world using `LoTM Game System`.
2. Open `Compendium Packs` in sidebar.
3. Import content from system packs as needed.
4. Create a `character` actor and drag pathway/ability/item content onto the actor sheet.
5. Use actor sheet actions for `Check`, `Ritual Risk`, `Artifact Backlash`, and corruption updates.

## Content Authoring Workflow

Source of truth is under `content-src/`:

- `content-src/pathways/`
- `content-src/abilities/`
- `content-src/items/`
- `content-src/rituals/`
- `content-src/artifacts/`
- `content-src/rolltables/`
- `content-src/actors/`
- `content-src/rules/`
- `content-src/configs/`

Validate and build packs:

```bash
python scripts/validate_content_source.py
python scripts/build_compendiums.py
```

Generated pack databases are written to `packs/*.db`.

## Verification Pipeline

```bash
python scripts/phase1_verification.py
python scripts/phase2_verification.py
python scripts/validate_content_source.py
python scripts/build_compendiums.py
python scripts/verify_foundry_manifest.py
python scripts/build_foundry_release.py
python scripts/rulebook_contract_audit.py --rulebook rulebook-source-v1.1.md
python scripts/rulebook_roundtrip_check.py --docx "LoTM Rulebook.docx"
```

Or run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_all_verification.ps1
```

## Release Process

1. Update `system.json`:
- bump `version`
- update `download` to `.../releases/download/vX.Y.Z/lotm-system-vX.Y.Z.zip`
2. Validate and build:

```bash
python scripts/validate_content_source.py
python scripts/build_compendiums.py
python scripts/verify_foundry_manifest.py
python scripts/build_foundry_release.py
```

3. Commit changes.
4. Create and push a tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

5. GitHub Actions publishes release assets:
- `system.json`
- `lotm-system-vX.Y.Z.zip`

## Troubleshooting

- If the repository is private, anonymous Foundry installs fail.
- If tag and `system.json.version` do not match, release workflow fails.
- If zip root folder is not `lotm-system/`, Foundry install/update fails.
- If `packs/*.db` are missing, compendium lists remain empty.
- If content semver/dependencies are invalid, content validation fails.