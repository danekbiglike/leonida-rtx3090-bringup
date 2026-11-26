[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RendererRepo,
    [Parameter(Mandatory)][string]$Destination,
    [ValidateSet('AVX2','Descriptors','Parallel','Joined','TextureLOD')][string]$Variant = 'AVX2'
)
$ErrorActionPreference = 'Stop'
$renderer = (Resolve-Path -LiteralPath $RendererRepo).Path
$destinationPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Destination)
if (Test-Path -LiteralPath $destinationPath) { throw "Choose a new worktree path: $destinationPath" }
$patchRoot = Join-Path (Split-Path -Parent $PSScriptRoot) 'patches'
$revision = '1ffff57a192c8a225118ae946ab21635c38442be'
$patches = @(
    'victory-rtx3090-paired-waves.patch',
    'upstream-pr1164-readback-pieces.patch',
    'victory-relay-merge-avx2.patch',
    'victory-separate-content-root.patch',
    'victory-window-pad-input.patch',
    'victory-keyboard-only.patch',
    'victory-keyboard-movement-3090.patch',
    'victory-offline-store.patch'
)
if ($Variant -in @('Descriptors', 'Parallel', 'Joined', 'TextureLOD')) { $patches += 'victory-descriptor-refresh-rtx3090.patch' }
if ($Variant -in @('Parallel', 'Joined', 'TextureLOD')) { $patches += 'victory-parallel-relay-rtx3090.patch' }
if ($Variant -in @('Joined', 'TextureLOD')) { $patches += 'victory-join-fetch-ranges-rtx3090.patch' }
if ($Variant -eq 'TextureLOD') {
    $patches += 'upstream-pr1210-resource-min-lod.patch', 'victory-recording-locks-rtx3090.patch'
}
foreach ($patch in $patches) {
    if (!(Test-Path -LiteralPath (Join-Path $patchRoot $patch) -PathType Leaf)) { throw "Missing patch $patch" }
}
& git -C $renderer cat-file -e "${revision}^{commit}"
if ($LASTEXITCODE) { throw "The renderer checkout needs revision $revision. Fetch the upstream revision and retry." }
& git -C $renderer worktree add --detach $destinationPath $revision
if ($LASTEXITCODE) { throw 'Git could not create the renderer worktree.' }
foreach ($patch in $patches) {
    & git -C $destinationPath apply --whitespace=nowarn (Join-Path $patchRoot $patch)
    if ($LASTEXITCODE) { throw "Patch $patch failed in $destinationPath. The worktree contains the earlier patches." }
}
Write-Output "Prepared $Variant renderer sources in $destinationPath"
