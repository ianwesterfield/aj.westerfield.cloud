$udp = New-Object System.Net.Sockets.UdpClient
$bytes = [System.Text.Encoding]::UTF8.GetBytes("FUNNEL_DISCOVER_PEERS")
$ep = [System.Net.IPEndPoint]::new([System.Net.IPAddress]::Loopback, 41420)
$udp.Client.ReceiveTimeout = 5000
$udp.Send($bytes, $bytes.Length, $ep) | Out-Null
Write-Host "Sent UDP to localhost:41420"
try {
    $remoteEP = $null
    $response = $udp.Receive([ref]$remoteEP)
    Write-Host "Got response: $([System.Text.Encoding]::UTF8.GetString($response))"
} catch {
    Write-Host "Error: $_"
}
$udp.Close()
