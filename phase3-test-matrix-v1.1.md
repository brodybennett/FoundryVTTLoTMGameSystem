# Phase 3 Test Matrix v1.1

## Pipeline and Publish Tests

1. Build script dependency check
- Fail with clear message when Pandoc is unavailable.

2. Deterministic build run
- Build `LoTM Rulebook.docx` from `rulebook-source-v1.1.md`.

3. Roundtrip audit
- Extract text from built docx and verify required canonical contract markers.

4. Consolidated gate ordering
- Verify `run_all_verification.ps1` executes checks in required order.

5. Failure propagation
- Any failed script must stop gate and return non-zero exit code.

## Acceptance

1. All verification stages pass.
2. Final docx includes canonical clamp/action/skill/corruption contract text.
3. Release docs reference v1.1 contracts and commands.

