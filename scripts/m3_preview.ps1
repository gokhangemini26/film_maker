# One Blender process per shot (a single long process produced garbage colours in EEVEE on Windows ARM).
param([string]$Shots = "all", [string]$Out = "prev", [string]$Width = "768", [string]$Project = "last_signal")
$root = Split-Path -Parent $PSScriptRoot
$blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$outdir = "$root\.fm_local\$Out"
$resolved = "$root\projects\$Project\09_resolved"
New-Item -ItemType Directory -Force $outdir | Out-Null
if ($Shots -eq "all") { $ids = Get-ChildItem "$resolved\SC*.json" | ForEach-Object { $_.BaseName } } else { $ids = $Shots.Split(",") }
foreach ($id in $ids) {
  & $blender -b --factory-startup --python "$root\blender\run_preview.py" -- $resolved $outdir $id $Width *>> "$root\.fm_local\$Out.log"
}
"DONE" | Out-File "$root\.fm_local\$Out.done"
