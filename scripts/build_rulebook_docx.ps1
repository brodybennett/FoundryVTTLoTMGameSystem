param(
  [string]$Source = "rulebook-source-v1.1.md",
  [string]$Output = "LoTM Rulebook.docx"
)

$ErrorActionPreference = "Stop"

$pandocExe = $null
$pandocCmd = Get-Command pandoc -ErrorAction SilentlyContinue
if ($pandocCmd) {
  $pandocExe = $pandocCmd.Source
} else {
  $fallback = Join-Path $env:LOCALAPPDATA "Pandoc\pandoc.exe"
  if (Test-Path $fallback) {
    $pandocExe = $fallback
  }
}

if (-not $pandocExe) {
  Write-Error "Pandoc is required but was not found in PATH or %LOCALAPPDATA%\\Pandoc\\pandoc.exe."
}

if (-not (Test-Path $Source)) {
  Write-Error "Source file not found: $Source"
}

if ((Test-Path $Output) -and (-not (Test-Path "LoTM Rulebook.docx.bak"))) {
  Copy-Item $Output "LoTM Rulebook.docx.bak" -Force
}

& $pandocExe --from gfm --to docx --standalone --output "$Output" "$Source"

if (-not (Test-Path $Output)) {
  Write-Error "Build failed; output file not found: $Output"
}

Write-Host "Built $Output from $Source"
