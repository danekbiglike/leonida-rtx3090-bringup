param([string]$FrameCsv)
. (Join-Path $PSScriptRoot 'rtx3090-paired-texture-lod.ps1') @PSBoundParameters
$env:VICTORY_CARD_BUFFERS_MIN_KB = '64'
$env:VICTORY_CARD_BUFFERS_MB = '1280'
$env:VICTORY_CARD_SYNC_BATCH = '1'
$env:VICTORY_COPY_CHANGED = '0'
