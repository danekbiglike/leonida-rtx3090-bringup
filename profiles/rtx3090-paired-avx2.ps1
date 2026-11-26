param([string]$FrameCsv)
. (Join-Path $PSScriptRoot 'rtx3090-paired-16k.ps1') @PSBoundParameters
$env:VICTORY_MERGE_AVX2 = '1'
