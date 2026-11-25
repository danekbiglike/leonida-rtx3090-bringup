# Dot-source in the same PowerShell session used to launch the patched renderer.
# Tested with the standalone paired-wave patch on 1ffff57a192c8a225118ae946ab21635c38442be.
param([string]$FrameCsv)
$env:VICTORY_WAVE_PAIRS = '1'
$env:VICTORY_BVH_BUILDER = '1'
$env:VICTORY_CARD_REHASH_RUNS = '1'
$env:VICTORY_BLACK_FRAME_PROBE = '0'
$env:VICTORY_MEMORY_MAP = '0'
$env:VICTORY_LOG = 'warn,victory_gpu::host=info'
$env:VICTORY_ASYNC_SUBMIT = '1'
$env:VICTORY_QUEUE2 = '1'
$env:VICTORY_INDIRECT_WINDOW = '1'
$env:VICTORY_INDIRECT_GATHER = '1'
$env:VICTORY_COPY_PLAIN = '1'
$env:VICTORY_JOIN_PARTS = '1'
$env:VICTORY_BACK_OWN_VIEW = '1'
$env:VICTORY_STAGING_POOL = '0'
$env:VICTORY_RELAY = '2'
$env:VICTORY_CARD_FETCH_INFLIGHT = '0'
if ($FrameCsv) { $env:VICTORY_FRAME_CSV = [IO.Path]::GetFullPath($FrameCsv) }
