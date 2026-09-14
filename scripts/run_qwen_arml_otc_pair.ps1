$ErrorActionPreference = "Stop"
$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location $RepoRoot
. (Join-Path $PSScriptRoot "Resolve-Python.ps1")
$PythonExe = Get-AgentOlympiadPython
# Load the selected provider configuration without printing credentials.
Get-Content (Join-Path $RepoRoot ".env") | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $name, $value = $line.Split("=", 2)
        Set-Item -Path "env:$($name.Trim())" -Value $value.Trim().Trim('"').Trim("'")
    }
}
if (-not $env:TINKER_API_KEY -or -not $env:TINKER_MODEL) {
    throw "Set TINKER_API_KEY and TINKER_MODEL in .env"
}
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputRoot = "results/arml_2009_tinker_otc_pair_manifest_$stamp"
Write-Output "PAIR_OUT=$outputRoot MODEL=$env:TINKER_MODEL"
foreach ($variant in @("vallina_otc", "otc")) {
    $variantOutput = Join-Path $outputRoot $variant
    & $PythonExe -u src/run_competition_batch.py --live --provider tinker `
        --contest-manifest data/contest_manifests/generated/arml_local_2009.json `
        --system-variant $variant --action-calling auto `
        --max-output-tokens 8192 --temperature 0.2 --max-turns 10 `
        --max-simulated-minutes 50 --deadline-submit --rules-mode enforced `
        --no-judge-task --no-judge-collab --no-judge-cce --output $variantOutput
    if ($LASTEXITCODE -ne 0) { throw "$variant failed: exit $LASTEXITCODE" }
    $result = Get-Content -Raw (Join-Path $variantOutput "contest_session.json") | ConvertFrom-Json
    if ($result.system_variant -ne $variant) { throw "Baseline mismatch for $variant" }
}
Write-Output "DONE_PAIR=$outputRoot"
