<#
.SYNOPSIS
    Build and push AJ base images to Docker Hub

.DESCRIPTION
    This script builds the base images (system deps + pip packages) and optionally
    pushes them to Docker Hub. Run this when requirements.txt changes.
    
    By default, it checks if local images match remote and skips unchanged images.

.PARAMETER Registry
    Docker Hub username or registry (default: "ianwesterfield")

.PARAMETER Push
    Push images to Docker Hub after building (default: true)

.PARAMETER Services
    Which services to build (default: all)

.PARAMETER Force
    Force rebuild and push even if images haven't changed

.EXAMPLE
    .\build-base-images.ps1

.EXAMPLE
    .\build-base-images.ps1 -Registry "yourusername" -Push

.EXAMPLE
    .\build-base-images.ps1 -Services "memory" -Force
#>

param(
  [string]$Registry = "ianwesterfield",
  [switch]$Push = $true,
  [string[]]$Services = @("memory", "extractor", "pragmatics"),
  [switch]$Force = $false
)

function Get-LocalImageDigest {
  param([string]$ImageName)
  $digest = docker images --format "{{.Digest}}" $ImageName 2>$null
  if ($digest -and $digest -ne "<none>") {
    return $digest
  }
  return $null
}

function Get-RemoteImageDigest {
  param([string]$ImageName)
  try {
    # Use docker manifest inspect to get remote digest
    $manifest = docker manifest inspect $ImageName 2>$null | ConvertFrom-Json
    if ($manifest -and $manifest.config -and $manifest.config.digest) {
      return $manifest.config.digest
    }
    # For multi-platform images, check the digest directly
    if ($manifest -and $manifest.manifests) {
      return "exists"  # Image exists but multi-platform
    }
  }
  catch {
    return $null
  }
  return $null
}

function Get-FileHash256 {
  param([string]$Path)
  if (Test-Path $Path) {
    return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.Substring(0, 12)
  }
  return "missing"
}

function Test-NeedsRebuild {
  param(
    [string]$Context,
    [string]$ImageName
  )
  
  $reqFile = Join-Path $Context "requirements.txt"
  $dockerFile = Join-Path $Context "Dockerfile.base"
  
  # Get file hashes for comparison
  $reqHash = Get-FileHash256 $reqFile
  $dockerHash = Get-FileHash256 $dockerFile
  
  # Check if local image exists
  $localExists = docker images -q $ImageName 2>$null
  if (-not $localExists) {
    return @{ NeedsBuild = $true; Reason = "Local image not found" }
  }
  
  # Check image labels for stored hashes (if we've built before with this script)
  $labels = docker inspect --format '{{json .Config.Labels}}' $ImageName 2>$null | ConvertFrom-Json
  if ($labels -and $labels.'aj.requirements.hash' -and $labels.'aj.dockerfile.hash') {
    if ($labels.'aj.requirements.hash' -ne $reqHash) {
      return @{ NeedsBuild = $true; Reason = "requirements.txt changed ($reqHash vs $($labels.'aj.requirements.hash'))" }
    }
    if ($labels.'aj.dockerfile.hash' -ne $dockerHash) {
      return @{ NeedsBuild = $true; Reason = "Dockerfile.base changed" }
    }
  }
  
  return @{ NeedsBuild = $false; Reason = "No changes detected" }
}

function Test-NeedsPush {
  param([string]$ImageName)
  
  # Get local digest
  $localDigest = docker images --format "{{.ID}}" $ImageName 2>$null
  if (-not $localDigest) {
    return @{ NeedsPush = $false; Reason = "No local image" }
  }
  
  # Check if remote exists by trying to pull manifest
  $remoteExists = docker manifest inspect $ImageName 2>$null
  if (-not $remoteExists) {
    return @{ NeedsPush = $true; Reason = "Remote image not found" }
  }
  
  # Compare creation times (rough heuristic)
  $localCreated = docker inspect --format '{{.Created}}' $ImageName 2>$null
  
  return @{ NeedsPush = $false; Reason = "Remote image exists (use -Force to push anyway)" }
}

$ErrorActionPreference = "Stop"

$ServiceConfig = @{
  "memory"     = @{
    Context    = "layers/memory"
    Dockerfile = "Dockerfile.base"
    ImageName  = "aj-memory-base"
  }
  "extractor"  = @{
    Context    = "layers/extractor"
    Dockerfile = "Dockerfile.base"
    ImageName  = "aj-extractor-base"
  }
  "pragmatics" = @{
    Context    = "layers/pragmatics"
    Dockerfile = "Dockerfile.base"
    ImageName  = "aj-pragmatics-base"
  }
}

Write-Host ""
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "  AJ Base Image Builder"  -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "Registry: $Registry"
Write-Host "Services: $($Services -join ', ')"
Write-Host "Push: $Push"
Write-Host "Force: $Force"
Write-Host ""

$startTime = Get-Date
$skippedBuilds = @()
$skippedPushes = @()

foreach ($service in $Services) {
  if (-not $ServiceConfig.ContainsKey($service)) {
    Write-Host "Unknown service: $service" -ForegroundColor Red
    continue
  }

  $config = $ServiceConfig[$service]
  $imageName = "$Registry/$($config.ImageName):latest"
  $contextPath = $config.Context

  Write-Host ""
  Write-Host "----------------------------------------" -ForegroundColor Yellow
  Write-Host "Checking: $imageName" -ForegroundColor Yellow
  Write-Host "----------------------------------------" -ForegroundColor Yellow

  # Check if rebuild needed
  $buildCheck = Test-NeedsRebuild -Context $contextPath -ImageName $imageName
  
  if (-not $Force -and -not $buildCheck.NeedsBuild) {
    Write-Host "  SKIP build: $($buildCheck.Reason)" -ForegroundColor DarkGray
    $skippedBuilds += $service
  }
  else {
    if ($Force) {
      Write-Host "  FORCE build requested" -ForegroundColor Magenta
    }
    else {
      Write-Host "  BUILD needed: $($buildCheck.Reason)" -ForegroundColor Yellow
    }

    $buildStart = Get-Date

    # Get file hashes to embed as labels
    $reqHash = Get-FileHash256 (Join-Path $contextPath "requirements.txt")
    $dockerHash = Get-FileHash256 (Join-Path $contextPath "Dockerfile.base")

    Push-Location $contextPath
    try {
      docker build -f $config.Dockerfile `
        --label "aj.requirements.hash=$reqHash" `
        --label "aj.dockerfile.hash=$dockerHash" `
        --label "aj.built=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" `
        -t $imageName .
      if ($LASTEXITCODE -ne 0) {
        throw "Build failed for $service"
      }
    }
    finally {
      Pop-Location
    }

    $buildTime = (Get-Date) - $buildStart
    Write-Host "  Built $service in $([math]::Round($buildTime.TotalSeconds, 1))s" -ForegroundColor Green
  }

  if ($Push) {
    # Check if push needed
    $pushCheck = Test-NeedsPush -ImageName $imageName
    
    if (-not $Force -and -not $pushCheck.NeedsPush -and $skippedBuilds -contains $service) {
      Write-Host "  SKIP push: $($pushCheck.Reason)" -ForegroundColor DarkGray
      $skippedPushes += $service
    }
    else {
      if ($Force) {
        Write-Host "  FORCE push requested" -ForegroundColor Magenta
      }
      elseif ($skippedBuilds -notcontains $service) {
        Write-Host "  PUSH needed: New build" -ForegroundColor Yellow
      }
      
      Write-Host "  Pushing: $imageName" -ForegroundColor Yellow
      docker push $imageName
      if ($LASTEXITCODE -ne 0) {
        throw "Push failed for $service"
      }
      Write-Host "  Pushed $service" -ForegroundColor Green
    }
  }
}

$totalTime = (Get-Date) - $startTime

Write-Host ""
Write-Host "========================================"  -ForegroundColor Green
Write-Host "  Build Complete!"  -ForegroundColor Green
Write-Host "========================================"  -ForegroundColor Green
Write-Host "Total time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes"

if ($skippedBuilds.Count -gt 0) {
  Write-Host "Skipped builds: $($skippedBuilds -join ', ')" -ForegroundColor DarkGray
}
if ($skippedPushes.Count -gt 0) {
  Write-Host "Skipped pushes: $($skippedPushes -join ', ')" -ForegroundColor DarkGray
}
Write-Host ""

if (-not $Push) {
  Write-Host "To push images to Docker Hub:" -ForegroundColor Yellow
  Write-Host '  .\build-base-images.ps1 -Push' -ForegroundColor Yellow
  Write-Host ""
}

Write-Host "To force rebuild all:" -ForegroundColor Cyan
Write-Host '  .\build-base-images.ps1 -Force' -ForegroundColor Cyan
Write-Host ""

Write-Host "To use these images in docker-compose:" -ForegroundColor Cyan
Write-Host "  docker compose up -d --build" -ForegroundColor Cyan
Write-Host ""
