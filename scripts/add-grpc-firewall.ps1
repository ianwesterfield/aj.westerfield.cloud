# Add firewall rule for FunnelCloud gRPC
# Run as Administrator

$ruleName = "FunnelCloud gRPC"

# Check if rule already exists
$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
  Write-Host "Rule '$ruleName' already exists" -ForegroundColor Yellow
}
else {
  New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -LocalPort 41235 -Protocol TCP -Action Allow -Profile Any
  Write-Host "Created firewall rule: $ruleName" -ForegroundColor Green
}

# Verify
Get-NetFirewallRule -DisplayName "*FunnelCloud*" | Format-Table DisplayName, Enabled, Direction, Action
