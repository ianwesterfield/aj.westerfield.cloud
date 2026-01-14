<#
.SYNOPSIS
    Deploys the AJ filter to Open-WebUI via API.

.DESCRIPTION
    Reads the aj.filter.py file and deploys it to Open-WebUI as a filter.
    Requires WEBUI_URL and WEBUI_API_KEY environment variables or secrets.

.EXAMPLE
    .\deploy-filter.ps1
#>

param(
  [string]$WebUIUrl = $env:WEBUI_URL,
  [string]$ApiKey = $env:WEBUI_API_KEY,
  [string]$FilterPath = "$PSScriptRoot\..\filters\aj.filter.py"
)

# Load from secrets if not provided
$secretsPath = "$PSScriptRoot\..\secrets"
if (-not $WebUIUrl) {
  $WebUIUrl = "http://localhost:8180"
}
if (-not $ApiKey -and (Test-Path "$secretsPath\webui_admin_api_key.txt")) {
  $ApiKey = Get-Content "$secretsPath\webui_admin_api_key.txt" -Raw
  $ApiKey = $ApiKey.Trim()
}

if (-not $ApiKey) {
  Write-Error "No API key found. Set WEBUI_API_KEY or create secrets/webui_admin_api_key.txt"
  exit 1
}

# Read filter content
if (-not (Test-Path $FilterPath)) {
  Write-Error "Filter not found: $FilterPath"
  exit 1
}

$filterContent = Get-Content $FilterPath -Raw
Write-Host "[INFO] Loaded filter: $FilterPath ($($filterContent.Length) chars)"

# Get existing filters to find AJ filter ID
Write-Host "[INFO] Checking for existing AJ filter..."
try {
  $headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type"  = "application/json"
  }
    
  $filtersResponse = Invoke-RestMethod -Uri "$WebUIUrl/api/v1/functions/" -Headers $headers -Method Get
  $ajFilter = $filtersResponse | Where-Object { $_.name -eq "AJ" -or $_.id -eq "aj_filter" }
    
  if ($ajFilter) {
    Write-Host "[OK] Found existing filter: $($ajFilter.id)"
    $filterId = $ajFilter.id
    $method = "Post"
    $endpoint = "$WebUIUrl/api/v1/functions/id/$filterId/update"
  }
  else {
    Write-Host "[INFO] Creating new filter..."
    $method = "Post"
    $endpoint = "$WebUIUrl/api/v1/functions/create"
  }
}
catch {
  Write-Host "[WARN] Could not list filters, attempting create: $_"
  $method = "Post"
  $endpoint = "$WebUIUrl/api/v1/functions/create"
  $filterId = $null
}

# Prepare filter payload
$payload = @{
  id      = "aj_filter"
  name    = "AJ"
  type    = "filter"
  content = $filterContent
  meta    = @{
    description = "AJ Knowledge-Centric AI Assistant - Intent routing, memory, and task orchestration"
  }
} | ConvertTo-Json -Depth 10

# Deploy
Write-Host "[DEPLOY] Deploying to $endpoint..."
try {
  $response = Invoke-RestMethod -Uri $endpoint -Headers $headers -Method $method -Body $payload
  Write-Host "[OK] Filter deployed successfully!"
  Write-Host "   ID: $($response.id)"
  Write-Host "   Name: $($response.name)"
}
catch {
  Write-Error "[FAIL] Deploy failed: $_"
  Write-Host "Response: $($_.Exception.Response)"
  exit 1
}

Write-Host ""
Write-Host "[DONE] Enable the filter in Open-WebUI: $WebUIUrl/admin/functions"
