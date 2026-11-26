param([string]$FrameCsv)
. (Join-Path $PSScriptRoot 'rtx3090-small-card-buffers.ps1') @PSBoundParameters
$env:VICTORY_CARD_HASH_LEN = '1'
