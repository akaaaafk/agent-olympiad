[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Model,
    [ValidateSet('tinker', 'perplexity', 'openai', 'openagents', 'vectorengine')]
    [string]$Provider = 'tinker',
    [string]$ApiKeyEnv = '',
    [string]$Output,
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($Model)) { throw 'Model must be specified.' }
if ($ApiKeyEnv -and [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($ApiKeyEnv, 'Process'))) {
    throw "Set the environment variable named by -ApiKeyEnv before running."
}
if ([string]::IsNullOrWhiteSpace($Output)) {
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
    $Output = Join-Path $Repo "results/arml_local_2009_decentralized_$Stamp"
}

$PreviousDataRoot = [Environment]::GetEnvironmentVariable('AGENT_OLYMPIAD_DATA_ROOT', 'Process')
$ExitCode = 1
Push-Location $Repo
try {
    # This edition is in the full catalog, independent of mini selection.
    $env:AGENT_OLYMPIAD_DATA_ROOT = Join-Path $Repo 'data'
    $RunArgs = @(
        'scripts/run_pipeline.py', 'all',
        '--competitions', 'arml_local',
        '--years', '2009',
        '--sessions', 'arml_local_2009',
        '--system-variant', 'decentralized',
        '--provider', $Provider,
        '--model', $Model,
        '--output', $Output
    )
    if ($ApiKeyEnv) { $RunArgs += @('--api-key-env', $ApiKeyEnv) }
    Write-Host "ARML Local 2009 / decentralized -> $Output"
    & $Python @RunArgs
    $ExitCode = $LASTEXITCODE
}
finally {
    [Environment]::SetEnvironmentVariable('AGENT_OLYMPIAD_DATA_ROOT', $PreviousDataRoot, 'Process')
    Pop-Location
}
exit $ExitCode
