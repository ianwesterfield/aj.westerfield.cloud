<#
.SYNOPSIS
    Upload only essential training files to GPU server (excludes large data files)

.DESCRIPTION
    Uploads ~5 MB of scripts/configs instead of ~24 GB of data.
    All training data is downloaded/generated on the server from HuggingFace.

.PARAMETER Server
    SSH connection string (e.g., "root@gpu-server.example.com" or "user@192.168.1.100")

.PARAMETER RemotePath
    Remote directory path (default: /workspace/training)

.PARAMETER KeyFile
    Optional SSH key file path

.EXAMPLE
    .\upload-training-minimal.ps1 -Server root@gpu.runpod.io -RemotePath /workspace/training

.EXAMPLE
    .\upload-training-minimal.ps1 -Server user@vast-ai-host -KeyFile ~/.ssh/vast_key
#>

param(
  [Parameter(Mandatory = $true)]
  [string]$Server,
    
  [Parameter(Mandatory = $false)]
  [string]$RemotePath = "/workspace/training",
    
  [Parameter(Mandatory = $false)]
  [string]$KeyFile
)

$ErrorActionPreference = "Stop"

# Paths
$TrainingDir = Join-Path $PSScriptRoot "..\training"
$TempDir = Join-Path $env:TEMP "aj-training-upload"
$TempZip = Join-Path $env:TEMP "aj-training-minimal.tar.gz"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "AJ Training Minimal Upload" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Clean up temp directory
if (Test-Path $TempDir) {
  Remove-Item -Recurse -Force $TempDir
}
New-Item -ItemType Directory -Path $TempDir | Out-Null

Write-Host "Copying essential files (excluding large data)..." -ForegroundColor Yellow

# Files/folders to include
$includes = @(
  "setup_and_train_v2.sh",
  "setup_digitalocean_h200.sh",
  "requirements.txt",
  "DEPLOY_V2.md",
  "README.md",
  "pytest.ini",
  "configs",
  "scripts",
  "datasets/*.py",
  "datasets/README.md",
  "agentic/configs",
  "agentic/converters",
  "agentic/generators",
  "agentic/schemas",
  "agentic/tasks",
  "agentic/utils",
  "agentic/*.py",
  "agentic/*.md"
)

# Copy structure
foreach ($pattern in $includes) {
  $sourcePath = Join-Path $TrainingDir $pattern
  $destPath = Join-Path $TempDir $pattern
    
  if (Test-Path $sourcePath) {
    $destDir = Split-Path $destPath -Parent
    if (-not (Test-Path $destDir)) {
      New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
        
    if ((Get-Item $sourcePath) -is [System.IO.DirectoryInfo]) {
      Copy-Item -Recurse -Path $sourcePath -Destination $destPath -Force
    }
    else {
      # Handle wildcards
      $files = Get-ChildItem -Path $sourcePath -ErrorAction SilentlyContinue
      foreach ($file in $files) {
        Copy-Item -Path $file.FullName -Destination $destDir -Force
      }
    }
  }
}

# Create datasets directory structure (empty, for downloads)
$datasetDirs = @("datasets/raw", "datasets/processed")
foreach ($dir in $datasetDirs) {
  $path = Join-Path $TempDir $dir
  if (-not (Test-Path $path)) {
    New-Item -ItemType Directory -Path $path -Force | Out-Null
    # Add .gitkeep
    New-Item -ItemType File -Path (Join-Path $path ".gitkeep") -Force | Out-Null
  }
}

# Calculate size
$totalSize = (Get-ChildItem -Recurse -Path $TempDir -File | Measure-Object -Property Length -Sum).Sum
$sizeMB = [math]::Round($totalSize / 1MB, 2)

Write-Host ""
Write-Host "Package size: $sizeMB MB" -ForegroundColor Green
Write-Host ""

# Build SSH/SCP options
$sshOpts = @()
if ($KeyFile) {
  $sshOpts += "-i", $KeyFile
}

# Check for rsync (preferred) or fall back to scp
$useRsync = Get-Command rsync -ErrorAction SilentlyContinue

if ($useRsync) {
  Write-Host "Uploading via rsync to $Server`:$RemotePath ..." -ForegroundColor Yellow
    
  $rsyncOpts = @("-avz", "--progress")
  if ($KeyFile) {
    $rsyncOpts += "-e", "ssh -i $KeyFile"
  }
    
  & rsync @rsyncOpts "$TempDir/" "${Server}:${RemotePath}/"
}
else {
  Write-Host "Uploading via scp to $Server`:$RemotePath ..." -ForegroundColor Yellow
  Write-Host "(Install rsync for faster uploads with progress)" -ForegroundColor DarkGray
    
  # Create remote directory
  & ssh @sshOpts $Server "mkdir -p $RemotePath"
    
  # Upload
  & scp @sshOpts -r "$TempDir\*" "${Server}:${RemotePath}/"
}

if ($LASTEXITCODE -eq 0) {
  Write-Host ""
  Write-Host "============================================" -ForegroundColor Green
  Write-Host "Upload complete!" -ForegroundColor Green
  Write-Host "============================================" -ForegroundColor Green
  Write-Host ""
  Write-Host "Next steps on the server:" -ForegroundColor Cyan
  Write-Host "  ssh $Server" -ForegroundColor White
  Write-Host "  cd $RemotePath" -ForegroundColor White
  Write-Host "  chmod +x setup_and_train_v2.sh" -ForegroundColor White
  Write-Host "  ./setup_and_train_v2.sh" -ForegroundColor White
  Write-Host ""
}
else {
  Write-Host "Upload failed!" -ForegroundColor Red
  exit 1
}

# Cleanup
Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
