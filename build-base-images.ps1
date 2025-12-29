<#
.SYNOPSIS
  Builds base images (system deps + pip packages) for AJ services.

.DESCRIPTION
  Run this script when requirements.txt changes for any service.
  Base images contain expensive pip installs; app images just COPY code.

.PARAMETER Registry
  Docker Hub username or registry (default: "ianwesterfield")

.PARAMETER Push
  Push images to Docker Hub after building (default: $true)

.PARAMETER Services
  Which services to build (default: all)

.EXAMPLE
  .\build-base-images.ps1
  .\build-base-images.ps1 -Registry "yourusername" -Push
  .\build-base-images.ps1 -Services "memory"
  .\build-base-images.ps1 -Services "executor", "orchestrator"
#>

param(
  [string]$Registry = "ianwesterfield",
  [switch]$Push = $true,
  [string[]]$Services = @("memory", "extractor", "pragmatics", "executor", "orchestrator")
)

$ErrorActionPreference = "Stop"

$ServiceConfig = @{
  "memory"       = @{
    Context    = "layers/memory"
    Dockerfile = "Dockerfile.base"
    ImageName  = "aj-memory-base"
  }
  "extractor"    = @{
    Context    = "layers/extractor"
    Dockerfile = "Dockerfile.base"
    ImageName  = "aj-extractor-base"
  }
  "pragmatics"   = @{
    Context    = "layers/pragmatics"
    Dockerfile = "Dockerfile.base"
    ImageName  = "aj-pragmatics-base"
  }
  "executor"     = @{
    Context    = "layers/executor"
    Dockerfile = "Dockerfile.base"
    ImageName  = "aj-executor-base"
  }
  "orchestrator" = @{
    Context    = "layers/orchestrator"
    Dockerfile = "Dockerfile.base"
    ImageName  = "aj-orchestrator-base"
  }
}

Write-Host ""
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "  AJ Base Image Builder"  -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "Registry: $Registry"
Write-Host "Services: $($Services -join ', ')"
Write-Host "Push: $Push"
Write-Host ""

$startTime = Get-Date

foreach ($service in $Services) {
  if (-not $ServiceConfig.ContainsKey($service)) {
    Write-Host "Unknown service: $service" -ForegroundColor Red
    continue
  }

  $config = $ServiceConfig[$service]
  $imageName = "$Registry/$($config.ImageName):latest"

  Write-Host ""
  Write-Host "----------------------------------------" -ForegroundColor Yellow
  Write-Host "Building: $imageName" -ForegroundColor Yellow
  Write-Host "----------------------------------------" -ForegroundColor Yellow

  $buildStart = Get-Date

  Push-Location $config.Context
  try {
    docker build -f $config.Dockerfile -t $imageName .
    if ($LASTEXITCODE -ne 0) {
      throw "Build failed for $service"
    }
  }
  finally {
    Pop-Location
  }

  $buildTime = (Get-Date) - $buildStart
  Write-Host "Built $service in $([math]::Round($buildTime.TotalSeconds, 1))s" -ForegroundColor Green

  if ($Push) {
    Write-Host "Pushing: $imageName" -ForegroundColor Yellow
    docker push $imageName
    if ($LASTEXITCODE -ne 0) {
      throw "Push failed for $service"
    }
    Write-Host "Pushed $service" -ForegroundColor Green
  }
}

$totalTime = (Get-Date) - $startTime

Write-Host ""
Write-Host "========================================"  -ForegroundColor Green
Write-Host "  Build Complete!"  -ForegroundColor Green
Write-Host "========================================"  -ForegroundColor Green
Write-Host "Total time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes"
Write-Host ""

if (-not $Push) {
  Write-Host "To push images to Docker Hub:" -ForegroundColor Yellow
  Write-Host '  .\build-base-images.ps1 -Registry "yourusername" -Push' -ForegroundColor Yellow
  Write-Host ""
}

Write-Host "To use these images in docker-compose:" -ForegroundColor Cyan
Write-Host "  docker compose up -d --build" -ForegroundColor Cyan
Write-Host ""
