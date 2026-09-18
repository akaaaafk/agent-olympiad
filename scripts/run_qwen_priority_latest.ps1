param(
    [ValidateSet('both', 'decentralized', 'centralized')]
    [string]$Variant = 'both',
    [string]$Model = 'Qwen/Qwen3.6-35B-A3B',
    [string]$JudgeProvider = 'tinker',
    [string]$JudgeModel = 'Qwen/Qwen3.6-35B-A3B',
    [string[]]$Competitions = @(
        'arml_local', 'arml_national_team', 'purple_comet', 'wmtc',
        'hmmt_guts', 'history_olympiad', 'qanta', 'science_bowl',
        'arml_national_power', 'arml_power', 'pumac_power',
        'iol_team', 'ioaa_group', 'ijso_practical', 'wsc_writing'
    ),
    [switch]$PlanOnly
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path (Split-Path -Parent $repoRoot) '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Python not found: $pythonPath"
}
$variants = if ($Variant -eq 'both') { @('decentralized', 'centralized') } else { @($Variant) }
$runTag = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
Push-Location $repoRoot
try {
    foreach ($systemVariant in $variants) {
        $outputPath = Join-Path $repoRoot "results\qwen_priority_latest_${systemVariant}_$runTag"
        if (Test-Path -LiteralPath $outputPath) { throw "Output already exists: $outputPath" }
        # Pipeline generates each native session manifest and passes --system-variant.
        # Centralized/decentralized default to rules off. Document tracks use
        # the current artifact runner and configured rubric rather than --schema.
        $cliArgs = @('-u', 'scripts\run_pipeline.py', 'all',
            '--competitions', ($Competitions -join ','),
            '--system-variant', $systemVariant,
            '--provider', 'tinker', '--model', $Model,
            '--judge-provider', $JudgeProvider, '--judge-model', $JudgeModel,
            '--output', $outputPath)
        Write-Host "Variant: $systemVariant"
        Write-Host "Contests: $($Competitions -join ',')"
        Write-Host "Output: $outputPath"
        if ($PlanOnly) {
            Write-Host ($pythonPath + ' ' + ($cliArgs -join ' '))
            continue
        }
        & $pythonPath @cliArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Pipeline exited $LASTEXITCODE. Inspect $outputPath\batch_status.json before proceeding."
        }
    }
}
finally { Pop-Location }
