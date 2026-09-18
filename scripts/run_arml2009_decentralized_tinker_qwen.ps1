[CmdletBinding()]
param(
    [string]$Output,
    [string]$Python = 'python'
)

# Matches TINKER_MODEL in the repository .env at the time this launcher was written.
# The Python entrypoint loads TINKER_API_KEY from .env; no key is stored here.
& (Join-Path $PSScriptRoot 'run_arml2009_decentralized.ps1') `
    -Provider 'tinker' `
    -Model 'Qwen/Qwen3.6-35B-A3B' `
    -Python $Python `
    -Output $Output
exit $LASTEXITCODE
