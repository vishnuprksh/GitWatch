# Candidate app.py locations (checked in order)
$candidateApps = @(
	(Join-Path $env:USERPROFILE 'OneDrive - Ship Watch\Desktop\Data Science\GitWatch\app.py'),
	(Join-Path $env:USERPROFILE 'Ship Watch\Vishnu Prakash - Data Science\GitWatch\app.py'),
	(Join-Path $env:USERPROFILE 'Ship Watch\sa_365backup - Ship-watch Shared\Reference Information\Data Science\GitWatch\app.py')
)

$app = $null
foreach ($p in $candidateApps) {
	if (Test-Path $p) { $app = $p; break }
}

if (-not $app) {
	Write-Error "No app.py found in candidate locations.`nChecked: $($candidateApps -join ', ')"
	exit 1
}

# Candidate python virtualenv executable
$pythonCandidates = @(
	(Join-Path $env:USERPROFILE 'local_projects\.global_env\Scripts\python.exe')
)

$pythonExe = $null
foreach ($p in $pythonCandidates) {
	if (Test-Path $p) { $pythonExe = $p; break }
}

if (-not $pythonExe) {
	$cmd = Get-Command python -ErrorAction SilentlyContinue
	if ($cmd) { $pythonExe = $cmd.Path }
}

if (-not $pythonExe) {
	Write-Error "Python executable not found. Please install Python or adjust the path."
	exit 1
}

Write-Output "Using Python: $pythonExe"
Write-Output "Running app: $app"

& "$pythonExe" "$app"
