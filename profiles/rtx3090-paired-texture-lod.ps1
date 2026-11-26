param([string]$FrameCsv)
. (Join-Path $PSScriptRoot 'rtx3090-paired-avx2.ps1') @PSBoundParameters
$env:VICTORY_WIDE_MERGE = '1'
$env:VICTORY_JOIN_FETCH_RANGES = '1'
$env:VICTORY_LAND_ASIDE = '1'
