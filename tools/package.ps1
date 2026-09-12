param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$UpstreamRef = "unknown"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$cfg = Get-Content (Join-Path $repo "upstream.json") -Raw | ConvertFrom-Json
$sha = (git -C $SourceRoot rev-parse --short=12 HEAD).Trim()
$safeRef = $UpstreamRef -replace '[^A-Za-z0-9._-]','-'
$version = "cn-$safeRef-$sha"
$upstreamPackager = Join-Path $SourceRoot "package_release.ps1"
if (-not (Test-Path -LiteralPath $upstreamPackager)) {
    throw "Fork package_release.ps1 not found: $upstreamPackager"
}
# Both maintained DLSSNR forks expose -Version and -SkipBuild. Their packager
# also enforces that proprietary nvngx_dlssnr.dll is never redistributed.
& $upstreamPackager -Version $version -SkipBuild
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$releaseDir = Join-Path $SourceRoot "release"
$sourceZip = Get-ChildItem -LiteralPath $releaseDir -Filter "*.zip" -File |
    Where-Object { $_.Name -like "*$version*" } |
    Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
if (-not $sourceZip) { throw "Upstream packager did not create a ZIP for $version" }
$stage = Join-Path $OutputDir "_stage"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
Expand-Archive -LiteralPath $sourceZip.FullName -DestinationPath $stage -Force
Copy-Item (Join-Path $repo "Localization\OptiScalerCN.ini") (Join-Path $stage "OptiScalerCN.ini") -Force
Copy-Item (Join-Path $repo "README.zh-CN.md") (Join-Path $stage "README.CN.zh-CN.md") -Force
Copy-Item (Join-Path $repo "UPSTREAM.md") (Join-Path $stage "UPSTREAM.CN.md") -Force
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$name = "$($cfg.package_prefix)-$safeRef-$sha.zip"
$zip = Join-Path $OutputDir $name
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
$hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
@{
    upstream_repository = $cfg.repository
    upstream_ref = $UpstreamRef
    upstream_commit = (git -C $SourceRoot rev-parse HEAD).Trim()
    package = (Split-Path -Leaf $zip)
    sha256 = $hash
    built_at_utc = (Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $OutputDir "build-metadata.json")
Remove-Item $stage -Recurse -Force
Write-Host "PACKAGE=$zip"
Write-Host "SHA256=$hash"
