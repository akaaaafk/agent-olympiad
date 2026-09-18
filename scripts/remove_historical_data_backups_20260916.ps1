$ErrorActionPreference = 'Stop'
$repoPath = 'E:\agent_olympiad\agent-olympiad'
$targetPath = 'E:\agent_olympiad\agent-olympiad\data\excluded'
$resolvedTarget = (Resolve-Path -LiteralPath $targetPath).Path
if ($resolvedTarget -ne $targetPath -or (Get-Item -LiteralPath $targetPath).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'Unexpected deletion target or reparse point'
}
$auditPath = Join-Path $repoPath ('docs\cleanup_audits\historical_backups_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Path $auditPath | Out-Null
$preserve = @(
    'formal_packet_review_20260911\manifest.json',
    'mystery_hunt_curated_exclusion_20260913\manifest.json',
    'ijso_answerless_years_20260913\manifest.json',
    'iol_answerless_years_20260913\manifest.json'
)
$preservedHashes = @{}
foreach ($relativePath in $preserve) {
    $sourcePath = Join-Path $targetPath $relativePath
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Missing audit manifest: $relativePath" }
    $copyPath = Join-Path $auditPath $relativePath
    New-Item -ItemType Directory -Path (Split-Path $copyPath) -Force | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $copyPath
    $preservedHashes[$relativePath] = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $copyPath -Algorithm SHA256).Hash -ne $preservedHashes[$relativePath]) { throw 'Audit manifest copy mismatch' }
}
$protectedPaths = @('data\benchmarks\index.json', 'data\viz\summary.json')
$protectedHashes = @{}
foreach ($relativePath in $protectedPaths) {
    $protectedHashes[$relativePath] = (Get-FileHash -LiteralPath (Join-Path $repoPath $relativePath) -Algorithm SHA256).Hash
}
$pendingDirs = [Collections.Generic.Stack[string]]::new()
$pendingDirs.Push($targetPath)
$inventoryWriter = [IO.StreamWriter]::new((Join-Path $auditPath 'deleted_inventory.csv'), $false, [Text.UTF8Encoding]::new($false))
$fileCount = 0L
$byteCount = 0L
try {
    $inventoryWriter.WriteLine('relative_path,bytes,last_write_utc,action')
    while ($pendingDirs.Count -gt 0) {
        $currentDir = [IO.DirectoryInfo]::new($pendingDirs.Pop())
        foreach ($entry in $currentDir.EnumerateFileSystemInfos()) {
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Refusing reparse point: $($entry.FullName)" }
            if ($entry.Attributes -band [IO.FileAttributes]::Directory) { $pendingDirs.Push($entry.FullName); continue }
            $relativePath = $entry.FullName.Substring($targetPath.Length + 1)
            $action = if ($preserve -contains $relativePath) { 'retain_audit_manifest' } else { 'delete' }
            $inventoryWriter.WriteLine(('"{0}",{1},"{2}",{3}' -f $relativePath.Replace('"','""'), $entry.Length, $entry.LastWriteTimeUtc.ToString('o'), $action))
            $fileCount++
            $byteCount += $entry.Length
        }
    }
} finally { $inventoryWriter.Dispose() }
$summary = [ordered]@{target=$targetPath;status='inventory_complete';files_before=$fileCount;bytes_before=$byteCount;retained_audit_manifests=$preserve;protected_sha256=$protectedHashes}
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $auditPath 'summary.json') -Encoding UTF8
Write-Output "Inventory saved: $auditPath; files=$fileCount; bytes=$byteCount"
if ((Resolve-Path -LiteralPath $targetPath).Path -ne 'E:\agent_olympiad\agent-olympiad\data\excluded') { throw 'Deletion target changed' }
Remove-Item -LiteralPath $targetPath -Recurse -Force
foreach ($relativePath in $preserve) {
    $restoredPath = Join-Path $targetPath $relativePath
    New-Item -ItemType Directory -Path (Split-Path $restoredPath) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $auditPath $relativePath) -Destination $restoredPath
    if ((Get-FileHash -LiteralPath $restoredPath -Algorithm SHA256).Hash -ne $preservedHashes[$relativePath]) { throw 'Restored audit manifest mismatch' }
}
foreach ($relativePath in $protectedPaths) {
    if ((Get-FileHash -LiteralPath (Join-Path $repoPath $relativePath) -Algorithm SHA256).Hash -ne $protectedHashes[$relativePath]) { throw 'Protected catalog changed' }
}
$remainingFiles = @(Get-ChildItem -LiteralPath $targetPath -Recurse -File)
if ($remainingFiles.Count -ne $preserve.Count) { throw 'Unexpected remaining backup files' }
$remainingBytes = ($remainingFiles | Measure-Object -Property Length -Sum).Sum
$summary.status = 'completed'
$summary.files_deleted = $fileCount - $remainingFiles.Count
$summary.bytes_deleted = $byteCount - $remainingBytes
$summary.bytes_retained = $remainingBytes
$summary.completed_utc = [DateTime]::UtcNow.ToString('o')
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $auditPath 'summary.json') -Encoding UTF8
$summary | ConvertTo-Json -Depth 5
