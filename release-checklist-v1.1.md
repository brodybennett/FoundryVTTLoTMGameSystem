# Release Checklist v1.1

## Pre-Release

1. Confirm v1 baseline files are unchanged and present.
2. Confirm v1.1 files exist and parse as valid JSON/Markdown.
3. Confirm `rulebook-source-v1.1.md` reflects canonical formulas and precedence.

## Verification Gate

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_all_verification.ps1
```

Expected:
- `ALL PHASE 1 CHECKS PASSED`
- `ALL PHASE 2 CHECKS PASSED`
- contract audit pass
- roundtrip check pass

## Publish

1. Build docx from markdown source.
2. Keep `LoTM Rulebook.docx.bak` unchanged as backup.
3. Confirm roundtrip check against final docx.

## Final Tag

Release tag target: `lotm-canon-v1.1.0`.

