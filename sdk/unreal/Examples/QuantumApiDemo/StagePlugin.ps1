# Copyright (c) 2026 David J. Grimsley. All rights reserved.
param(
    [string]$PluginSource = (Join-Path $PSScriptRoot '..\\..')
)

$resolvedSource = (Resolve-Path -LiteralPath $PluginSource).Path
$pluginDescriptor = Join-Path $resolvedSource 'QuantumApi.uplugin'
if (-not (Test-Path -LiteralPath $pluginDescriptor)) {
    throw "QuantumApi.uplugin was not found at '$resolvedSource'."
}

$demoRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$pluginDestination = Join-Path $demoRoot 'Plugins\\QuantumApi'
if (Test-Path -LiteralPath $pluginDestination) {
    $resolvedDestination = (Resolve-Path -LiteralPath $pluginDestination).Path
    if (-not $resolvedDestination.StartsWith($demoRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clear staging path outside the demo project: '$resolvedDestination'."
    }
    Remove-Item -LiteralPath $resolvedDestination -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $pluginDestination | Out-Null

$distributionEntries = @(
    'QuantumApi.uplugin',
    'README.md',
    'Binaries',
    'Config',
    'Content',
    'Docs',
    'Resources',
    'Source',
    'contract'
)
foreach ($entry in $distributionEntries) {
    $sourcePath = Join-Path $resolvedSource $entry
    if (Test-Path -LiteralPath $sourcePath) {
        Copy-Item -LiteralPath $sourcePath -Destination $pluginDestination -Recurse -Force
    }
}

# BuildPlugin may rewrite the patch component to 0. Keep the tested source version in the staged descriptor.
$authoredDescriptor = Join-Path $PSScriptRoot '..\..\QuantumApi.uplugin'
$authoredMetadata = Get-Content -LiteralPath $authoredDescriptor -Raw | ConvertFrom-Json
if (-not $authoredMetadata.EngineVersion) {
    throw "The authored plugin descriptor must declare EngineVersion."
}
$stagedDescriptor = Join-Path $pluginDestination 'QuantumApi.uplugin'
$stagedMetadata = Get-Content -LiteralPath $stagedDescriptor -Raw | ConvertFrom-Json
if (-not $stagedMetadata.EngineVersion) {
    throw "The staged plugin descriptor must declare EngineVersion."
}
if ($stagedMetadata.EngineVersion -ne $authoredMetadata.EngineVersion) {
    $stagedMetadata.EngineVersion = $authoredMetadata.EngineVersion
    $json = $stagedMetadata | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText($stagedDescriptor, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}
Write-Host "Staged QuantumApi plugin at $pluginDestination"
