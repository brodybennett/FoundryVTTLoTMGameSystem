# LoTM Game System for Foundry VTT

FoundryVTT game system package for a Lord of the Mysteries-inspired TTRPG.

## Install in Foundry

In Foundry VTT:

1. Open `Game Systems`.
2. Click `Install System`.
3. Paste this Manifest URL:

`https://github.com/brodybennett/FoundryVTTLoTMGameSystem/releases/latest/download/system.json`

## Compendium Structure

The system publishes unified compendiums in this access layout:

- `Pathways (All)` (all pathway roots and sequence nodes in one pack; filter by pathway)
- `Items (All Types)` (weapons, armor, gear/features, consumables, ingredients, and other item subtypes in one pack)
- `Sealed Artifacts` (cross-pathway, grouped by sequence in naming/flags)
- `Abilities (All Pathways)` (grouped by pathway + sequence in naming/flags)
- `Rituals (All Pathways)` (pathway/universal grouping supported)
- `Roll Tables (All Segments)` (resources, abilities, rituals, artifacts, corruption, encounters in one pack)
- `Actors (All Categories)` (factions, beyonder monsters, civilians in one pack)
- `Rules: Hyperlinked Reference` (JournalEntry rules compendium with table-of-contents links)

Compendium folder UX is native and auto-organized on world ready for GMs:

- `Pathways (All)`: folder per pathway containing pathway root + its sequence nodes
- `Roll Tables (All Segments)`: folder per segment (`Resources`, `Abilities`, `Rituals`, `Artifacts`, `Corruption`, `Encounters`)
- `Items (All Types)`: folder per item group (`Weapons`, `Armor`, `Gear & Features`, `Consumables`, `Ingredients`, `Other`)
- `Actors (All Categories)`: folder per category (`Faction NPCs`, `Beyonder Monsters`, `Civilians`, `Other`)

Controls:

- World setting: `lotm-system.autoOrganizeCompendiums` (default `true`)
- Manual re-sync: `game.lotm.organizeCompendiums()`

## Create a Playable World

1. Create a world using `LoTM Game System`.
2. Open `Compendium Packs` in sidebar.
3. Import content from system packs as needed.
4. Create a `character` actor and drag pathway/ability/item content onto the actor sheet.
5. Use actor sheet actions for `Check`, `Ritual Risk`, `Artifact Backlash`, and corruption updates.

## Character Progression Workflow (Drag-and-Drop)

For `character` actors, progression is drag/drop-first and mirrors DnD5e-style sheet flow:

1. Open a character sheet and use the DnD5e-style tabs (`Details`, `Inventory`, `Features`, `Spells`, `Effects`, `Biography`, `Special Traits`).
2. Drag compendium/world items onto the actor:
   - `pathway`, `sequenceNode` -> class/sequence presentation in Features + header badge
   - `ability`, `ritual` -> `Spells` tab
   - `weapon`, `armor`, `gear`, `consumable`, `ingredient`, `artifact` -> `Inventory` tab
   - `feature`, `background`, `conditionTemplate` -> `Features` tab
3. Use roll controls directly from sidebar/header/details (`Check`, `Ritual Risk`, `Artifact Backlash`).
4. Use basic item favorites from the sidebar (`flags.lotm-system.favorites.items`).

Notes:
- Character sheet no longer exposes a creation wizard/finalize workflow.
- Roll automation no longer blocks on visible creation workflow state.
- `system.creation` metadata remains for compatibility and is normalized to hidden-complete state.
- Dropping/removing `pathway` or `sequenceNode` items auto-syncs:
  - `system.identity.pathwayId`
  - `system.identity.sequence`
- Repair/migration paths continue to seed missing defaults and legacy skill records.

Runtime helper APIs:

- `game.lotm.validateCreationStep(actor, step)`
- `game.lotm.getPathwayOptions()`
- `game.lotm.getSequenceOptions(pathwayId)`

## Sheet QA Workflow

For every sheet milestone/rework, use:

- `docs/sheet-ux-rubric.md` for pass/fail UX quality gating.
- `docs/sheet-review-checklist.md` for screenshot packet and manual test script.

Recommended review flow:

1. Update from latest tag build in Foundry.
2. Run checklist steps in-world.
3. Capture required screenshots + first console error (if any).
4. Return notes on confusion/noise/friction by tab/section.

## Roll Table Automation

Roll table source entries require strict `segment` and `formula` contracts. Runtime hooks map:

- `ritualFailure -> rituals`
- `artifactBacklash -> artifacts`
- `corruptionThresholdCross -> corruption`

Runtime APIs:

- `game.lotm.rollOnSegment(segment, context={})`
- `game.lotm.rollOnTableId(contentId, context={})`

Automation behavior by world setting:

- `full`: auto-draw table
- `assisted`: prompt before draw
- `manual`: resolve target table without drawing

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

Typed scaffolding and metadata tooling:

```bash
python scripts/content_tool.py new --type ability --id ability.example.new --name "New Ability"
python scripts/content_tool.py new-pathway-bundle --pathway-id pathway.example --pathway-name Example --top-sequence 9 --bottom-sequence 7
python scripts/content_tool.py bump-max-tested --version 1.2.13
python scripts/content_tool.py bump-max-tested --version 1.2.13 --write
```

Item authoring sheet is subtype-aware and exposes:

- type-relevant payload editors only
- CSV editors for `tags`, `allowedPathwayIds`, `requiresIds`, and sequence milestones
- structured effects row add/remove scaffold

## Verification Pipeline

```bash
python scripts/phase1_verification.py
python scripts/phase2_verification.py
python scripts/check_version_consistency.py
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
- If compendium folders are missing or stale, run `game.lotm.organizeCompendiums()` as GM.
- If content semver/dependencies are invalid, content validation fails.
- If sheets feel broken after update, hard-refresh Foundry client (`Ctrl+F5`) and re-test double-click open flow.
