param(
    [string]$PluginSource = (Join-Path $PSScriptRoot '..\\..')
)

$resolvedSource = (Resolve-Path -LiteralPath $PluginSource).Path
$pluginDescriptor = Join-Path $resolvedSource 'QuantumApi.uplugin'
if (-not (Test-Path -LiteralPath $pluginDescriptor)) {
    throw "QuantumApi.uplugin was not found at '$resolvedSource'."
}

$pluginDestination = Join-Path $PSScriptRoot 'Plugins\\QuantumApi'
New-Item -ItemType Directory -Force -Path $pluginDestination | Out-Null
Get-ChildItem -LiteralPath $resolvedSource -Force | Copy-Item -Destination $pluginDestination -Recurse -Force
Write-Host "Staged QuantumApi plugin at $pluginDestination"
