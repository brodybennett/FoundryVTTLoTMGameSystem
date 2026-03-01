# LoTM Game System for Foundry VTT

FoundryVTT game system package for a Lord of the Mysteries-inspired TTRPG.

## Install in Foundry

In Foundry VTT:

1. Open `Game Systems`.
2. Click `Install System`.
3. Paste this Manifest URL:

`https://github.com/brodybennett/FoundryVTTLoTMGameSystem/releases/latest/download/system.json`

## Release Process

1. Update `system.json`:
- bump `version`
- update `download` to match the new tag and zip filename
2. Commit changes.
3. Create and push a tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

4. GitHub Actions workflow publishes release assets:
- `system.json`
- `lotm-system-vX.Y.Z.zip`

## Troubleshooting

- If the repository is private, anonymous Foundry installs will fail.
- If tag and `system.json.version` do not match, release workflow fails.
- If zip root folder is not `lotm-system/`, Foundry install/update may fail.
