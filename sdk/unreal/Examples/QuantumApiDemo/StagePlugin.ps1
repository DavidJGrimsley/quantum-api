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
Write-Host "Staged QuantumApi plugin at $pluginDestination"
