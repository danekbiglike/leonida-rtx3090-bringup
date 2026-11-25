# Dot-source from a fresh PowerShell session in the same process as the launcher.
param([string]$FrameCsv)
. (Join-Path $PSScriptRoot 'rtx3090-paired-queue.ps1') @PSBoundParameters
$env:VICTORY_CARD_PIECE_KB = '16'
$env:VICTORY_CARD_WINDOWS_MB = '2048'
$env:VICTORY_LEVELS_ON_DEMAND = '1'
