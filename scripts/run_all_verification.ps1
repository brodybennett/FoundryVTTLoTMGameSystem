$ErrorActionPreference = "Stop"

function Run-Step {
  param(
    [string]$Name,
    [string]$Command
  )
  Write-Host "==> $Name"
  Invoke-Expression $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed with exit code $LASTEXITCODE"
  }
}

Run-Step "Phase 1 Verification" "python scripts/phase1_verification.py"
Run-Step "Phase 2 Verification" "python scripts/phase2_verification.py"
Run-Step "Rulebook Contract Audit" "python scripts/rulebook_contract_audit.py --rulebook rulebook-source-v1.1.md"
Run-Step "Rulebook Roundtrip Check" "python scripts/rulebook_roundtrip_check.py --docx `"LoTM Rulebook.docx`""

Write-Host "ALL VERIFICATION STAGES PASSED"

