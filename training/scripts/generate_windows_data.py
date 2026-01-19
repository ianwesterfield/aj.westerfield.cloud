#!/usr/bin/env python3
"""
Windows System Administration Training Data Generator
Target: ~400 examples for PowerShell, system management, registry, services
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for Windows system administration.
You help with PowerShell scripting, system configuration, services, registry, and Windows management tasks."""

# =============================================================================
# TOOL SELECTION TASKS - PowerShell Commands
# =============================================================================

BASIC_POWERSHELL_TASKS = [
    {
        "instruction": "List all files in the current directory",
        "command": "Get-ChildItem",
        "explanation": "Lists directory contents. Aliases: dir, ls, gci"
    },
    {
        "instruction": "Show running processes",
        "command": "Get-Process",
        "explanation": "Lists all running processes with CPU and memory usage"
    },
    {
        "instruction": "Get system information",
        "command": "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsHardwareAbstractionLayer",
        "explanation": "Retrieves detailed Windows system information"
    },
    {
        "instruction": "Check available disk space",
        "command": "Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{N='Used(GB)';E={[math]::Round($_.Used/1GB,2)}}, @{N='Free(GB)';E={[math]::Round($_.Free/1GB,2)}}",
        "explanation": "Shows disk usage for all mounted drives"
    },
    {
        "instruction": "Find large files over 100MB",
        "command": "Get-ChildItem -Path C:\\ -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Length -gt 100MB} | Sort-Object Length -Descending | Select-Object -First 20 FullName, @{N='Size(MB)';E={[math]::Round($_.Length/1MB,2)}}",
        "explanation": "Recursively searches for files larger than 100MB"
    },
    {
        "instruction": "Check Windows updates status",
        "command": "Get-WindowsUpdate -MicrosoftUpdate",
        "explanation": "Shows available Windows updates (requires PSWindowsUpdate module)"
    },
    {
        "instruction": "List installed programs",
        "command": "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate | Sort-Object DisplayName",
        "explanation": "Lists installed programs from registry"
    },
    {
        "instruction": "Show network adapters and their IP addresses",
        "command": "Get-NetIPAddress | Where-Object {$_.AddressFamily -eq 'IPv4'} | Select-Object InterfaceAlias, IPAddress, PrefixLength",
        "explanation": "Lists network adapters with IPv4 addresses"
    },
    {
        "instruction": "Check current user and permissions",
        "command": "[System.Security.Principal.WindowsIdentity]::GetCurrent().Name; whoami /groups",
        "explanation": "Shows current user and group memberships"
    },
    {
        "instruction": "View environment variables",
        "command": "Get-ChildItem Env: | Sort-Object Name",
        "explanation": "Lists all environment variables"
    },
    {
        "instruction": "Show listening ports",
        "command": "Get-NetTCPConnection -State Listen | Select-Object LocalAddress, LocalPort, OwningProcess, @{N='Process';E={(Get-Process -Id $_.OwningProcess).ProcessName}}",
        "explanation": "Lists all TCP ports in listening state with process info"
    },
    {
        "instruction": "Check Windows Defender status",
        "command": "Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled, AntivirusSignatureLastUpdated",
        "explanation": "Shows Windows Defender protection status"
    },
    {
        "instruction": "Copy a file to another location",
        "command": "Copy-Item -Path 'C:\\Source\\file.txt' -Destination 'C:\\Backup\\file.txt'",
        "explanation": "Copies file preserving attributes. Use -Recurse for directories"
    },
    {
        "instruction": "Move a file or folder",
        "command": "Move-Item -Path 'C:\\Old\\file.txt' -Destination 'C:\\New\\file.txt'",
        "explanation": "Moves/renames files or directories"
    },
    {
        "instruction": "Delete a file",
        "command": "Remove-Item -Path 'C:\\Temp\\oldfile.txt' -Force",
        "explanation": "Deletes file. -Force removes read-only files"
    },
    {
        "instruction": "Create a new directory",
        "command": "New-Item -Path 'C:\\Projects\\NewFolder' -ItemType Directory",
        "explanation": "Creates a new folder. Creates parent directories automatically"
    },
    {
        "instruction": "Create a new empty file",
        "command": "New-Item -Path 'C:\\Projects\\newfile.txt' -ItemType File",
        "explanation": "Creates empty file. Use Set-Content to add content"
    },
    {
        "instruction": "Read file contents",
        "command": "Get-Content -Path 'C:\\Logs\\app.log'",
        "explanation": "Reads file line by line. Use -Raw for entire content as string"
    },
    {
        "instruction": "Write text to a file",
        "command": "Set-Content -Path 'C:\\output.txt' -Value 'Hello World'",
        "explanation": "Writes content to file, overwriting existing. Use Add-Content to append"
    },
    {
        "instruction": "Append text to a file",
        "command": "Add-Content -Path 'C:\\Logs\\app.log' -Value 'New log entry'",
        "explanation": "Appends text to existing file without overwriting"
    },
    {
        "instruction": "Search for text in files",
        "command": "Select-String -Path 'C:\\Logs\\*.log' -Pattern 'error' -CaseSensitive",
        "explanation": "Grep-like text search across files. Returns matches with line numbers"
    },
    {
        "instruction": "Get current date and time",
        "command": "Get-Date",
        "explanation": "Returns current date/time. Format with: Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"
    },
    {
        "instruction": "Calculate time difference",
        "command": "(Get-Date) - (Get-Date '2024-01-01')",
        "explanation": "Returns TimeSpan showing days, hours, minutes between dates"
    },
    {
        "instruction": "Get file hash for verification",
        "command": "Get-FileHash -Path 'C:\\Downloads\\file.exe' -Algorithm SHA256",
        "explanation": "Computes cryptographic hash. Supports MD5, SHA1, SHA256, SHA512"
    },
    {
        "instruction": "Compare two files",
        "command": "Compare-Object (Get-Content file1.txt) (Get-Content file2.txt)",
        "explanation": "Shows differences between files. <= means in first, => means in second"
    },
    {
        "instruction": "Get file properties and metadata",
        "command": "Get-Item 'C:\\file.txt' | Select-Object Name, Length, CreationTime, LastWriteTime, Attributes",
        "explanation": "Retrieves file metadata including size and timestamps"
    },
    {
        "instruction": "Find files modified in last 24 hours",
        "command": "Get-ChildItem -Path C:\\ -Recurse -File | Where-Object {$_.LastWriteTime -gt (Get-Date).AddDays(-1)}",
        "explanation": "Finds recently modified files across a directory tree"
    },
    {
        "instruction": "Count files in a directory",
        "command": "(Get-ChildItem -Path 'C:\\Projects' -Recurse -File).Count",
        "explanation": "Returns total count of files including subdirectories"
    },
    {
        "instruction": "Get total size of a folder",
        "command": "(Get-ChildItem -Path 'C:\\Projects' -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB",
        "explanation": "Calculates total folder size in GB"
    },
    {
        "instruction": "List only directories",
        "command": "Get-ChildItem -Path 'C:\\' -Directory",
        "explanation": "Lists only folders, excluding files"
    },
    {
        "instruction": "List only files with specific extension",
        "command": "Get-ChildItem -Path 'C:\\Projects' -Filter '*.cs' -Recurse",
        "explanation": "Finds all C# files recursively"
    },
    {
        "instruction": "Clear the terminal screen",
        "command": "Clear-Host",
        "explanation": "Clears PowerShell console. Aliases: cls, clear"
    },
    {
        "instruction": "Get command history",
        "command": "Get-History",
        "explanation": "Shows recent commands. Use Invoke-History # to re-run a command"
    },
    {
        "instruction": "Get help for a command",
        "command": "Get-Help Get-Process -Full",
        "explanation": "Shows detailed help with examples. Update-Help downloads latest docs"
    },
    {
        "instruction": "List available commands",
        "command": "Get-Command -Module Microsoft.PowerShell.Management",
        "explanation": "Lists cmdlets in a module. Omit -Module to see all"
    },
    {
        "instruction": "Find commands by pattern",
        "command": "Get-Command *service*",
        "explanation": "Finds all commands containing 'service'"
    },
    {
        "instruction": "Check if a path exists",
        "command": "Test-Path -Path 'C:\\Windows\\System32'",
        "explanation": "Returns True/False if path exists"
    },
    {
        "instruction": "Get current working directory",
        "command": "Get-Location",
        "explanation": "Shows current path. Alias: pwd"
    },
    {
        "instruction": "Change directory",
        "command": "Set-Location -Path 'C:\\Projects'",
        "explanation": "Changes working directory. Alias: cd"
    },
    {
        "instruction": "Get hostname",
        "command": "$env:COMPUTERNAME",
        "explanation": "Returns the computer name from environment variable"
    },
    {
        "instruction": "Get current username",
        "command": "$env:USERNAME",
        "explanation": "Returns current user from environment variable"
    },
    {
        "instruction": "Set an environment variable",
        "command": "$env:MY_VAR = 'myvalue'",
        "explanation": "Sets environment variable for current session only"
    },
    {
        "instruction": "Set permanent environment variable",
        "command": "[Environment]::SetEnvironmentVariable('MY_VAR', 'myvalue', 'User')",
        "explanation": "Sets persistent user environment variable. Use 'Machine' for system-wide"
    },
    {
        "instruction": "Ping a host",
        "command": "Test-Connection -ComputerName 'google.com' -Count 4",
        "explanation": "PowerShell equivalent of ping command"
    },
    {
        "instruction": "Resolve DNS name",
        "command": "Resolve-DnsName -Name 'google.com'",
        "explanation": "DNS lookup returning IP addresses and record types"
    },
    {
        "instruction": "Download a file from URL",
        "command": "Invoke-WebRequest -Uri 'https://example.com/file.zip' -OutFile 'C:\\Downloads\\file.zip'",
        "explanation": "Downloads file from web. Use -UseBasicParsing for faster downloads"
    },
    {
        "instruction": "Make an HTTP GET request",
        "command": "Invoke-RestMethod -Uri 'https://api.github.com/users/octocat'",
        "explanation": "Makes REST API call and parses JSON response automatically"
    },
    {
        "instruction": "Start a process",
        "command": "Start-Process -FilePath 'notepad.exe' -ArgumentList 'C:\\file.txt'",
        "explanation": "Launches application. Use -Wait to block until it exits"
    },
    {
        "instruction": "Stop a process by name",
        "command": "Stop-Process -Name 'notepad' -Force",
        "explanation": "Kills all processes matching name"
    },
    {
        "instruction": "Get process by ID",
        "command": "Get-Process -Id 1234",
        "explanation": "Retrieves specific process by PID"
    },
    {
        "instruction": "Get top CPU consuming processes",
        "command": "Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet64",
        "explanation": "Lists processes by CPU usage"
    },
    {
        "instruction": "Get top memory consuming processes",
        "command": "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,2)}}",
        "explanation": "Lists processes by memory usage in MB"
    },
    {
        "instruction": "Check if a port is open",
        "command": "Test-NetConnection -ComputerName 'server' -Port 443",
        "explanation": "Tests TCP connectivity to specific port"
    },
    {
        "instruction": "Get local IP addresses",
        "command": "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notmatch 'Loopback'}).IPAddress",
        "explanation": "Lists all local IPv4 addresses excluding loopback"
    },
    {
        "instruction": "Get MAC address",
        "command": "Get-NetAdapter | Select-Object Name, MacAddress, Status",
        "explanation": "Lists network adapters with MAC addresses"
    },
    {
        "instruction": "Flush DNS cache",
        "command": "Clear-DnsClientCache",
        "explanation": "Clears local DNS resolver cache"
    },
    {
        "instruction": "Show routing table",
        "command": "Get-NetRoute | Where-Object {$_.DestinationPrefix -ne '::1/128' -and $_.DestinationPrefix -ne '127.0.0.1/32'}",
        "explanation": "Displays network routing table"
    },
    {
        "instruction": "Create a zip archive",
        "command": "Compress-Archive -Path 'C:\\Folder' -DestinationPath 'C:\\Archive.zip'",
        "explanation": "Creates zip file from folder or files"
    },
    {
        "instruction": "Extract a zip archive",
        "command": "Expand-Archive -Path 'C:\\Archive.zip' -DestinationPath 'C:\\Extracted'",
        "explanation": "Extracts zip file contents"
    },
    {
        "instruction": "Generate a random password",
        "command": "-join ((33..126) | Get-Random -Count 16 | ForEach-Object {[char]$_})",
        "explanation": "Generates 16-character random password from printable ASCII"
    },
    {
        "instruction": "Convert string to Base64",
        "command": "[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes('Hello World'))",
        "explanation": "Encodes text as Base64"
    },
    {
        "instruction": "Decode Base64 string",
        "command": "[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('SGVsbG8gV29ybGQ='))",
        "explanation": "Decodes Base64 back to text"
    },
    {
        "instruction": "Get clipboard contents",
        "command": "Get-Clipboard",
        "explanation": "Retrieves current clipboard text"
    },
    {
        "instruction": "Copy text to clipboard",
        "command": "'Hello World' | Set-Clipboard",
        "explanation": "Copies text to Windows clipboard"
    },
    {
        "instruction": "List installed PowerShell modules",
        "command": "Get-InstalledModule",
        "explanation": "Shows modules installed via PowerShellGet"
    },
    {
        "instruction": "Install a PowerShell module",
        "command": "Install-Module -Name Az -Scope CurrentUser -Force",
        "explanation": "Installs module from PowerShell Gallery"
    },
    {
        "instruction": "Update all installed modules",
        "command": "Get-InstalledModule | Update-Module",
        "explanation": "Updates all PowerShell Gallery modules to latest versions"
    },
    {
        "instruction": "Check PowerShell version",
        "command": "$PSVersionTable",
        "explanation": "Shows PowerShell version and related info"
    },
    {
        "instruction": "Get uptime",
        "command": "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime",
        "explanation": "Shows time since last boot"
    },
    {
        "instruction": "Restart the computer",
        "command": "Restart-Computer -Force",
        "explanation": "Reboots immediately. Use -WhatIf to preview"
    },
    {
        "instruction": "Shutdown the computer",
        "command": "Stop-Computer -Force",
        "explanation": "Shuts down immediately"
    },
    {
        "instruction": "Lock the workstation",
        "command": "rundll32.exe user32.dll,LockWorkStation",
        "explanation": "Locks Windows session"
    },
    {
        "instruction": "Get logged on users",
        "command": "query user",
        "explanation": "Shows users logged into the machine"
    },
    # Directory size commands - critical for disk analysis
    {
        "instruction": "List the largest directories on C: drive",
        "command": "Get-ChildItem -Path C:\\ -Directory -ErrorAction SilentlyContinue | ForEach-Object { $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; [PSCustomObject]@{Name=$_.Name; SizeMB=[math]::Round($size/1MB,2)} } | Sort-Object SizeMB -Descending | Select-Object -First 10",
        "explanation": "Calculates actual directory sizes by summing all files recursively, then sorts by size"
    },
    {
        "instruction": "Find the five largest folders on my drive",
        "command": "Get-ChildItem -Path C:\\ -Directory | ForEach-Object { [PSCustomObject]@{Path=$_.FullName; SizeGB=[math]::Round(((Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1GB),2)} } | Sort-Object SizeGB -Descending | Select-Object -First 5",
        "explanation": "Recursively calculates folder sizes in GB - note directories don't have a Length property, must sum files"
    },
    {
        "instruction": "Show directory sizes sorted by size",
        "command": "Get-ChildItem -Directory | ForEach-Object { $s = (Get-ChildItem $_ -Recurse -File -EA 0 | Measure-Object Length -Sum).Sum; [PSCustomObject]@{Name=$_.Name; 'Size(MB)'=[math]::Round($s/1MB,2)} } | Sort-Object 'Size(MB)' -Descending",
        "explanation": "Lists all subdirectories with their total sizes. Uses -EA 0 shorthand for -ErrorAction SilentlyContinue"
    },
    {
        "instruction": "What are the biggest folders taking up space?",
        "command": "Get-ChildItem C:\\ -Directory -ErrorAction SilentlyContinue | ForEach-Object { $size = 0; Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { $size += $_.Length }; [PSCustomObject]@{Folder=$_.Name; SizeMB=[math]::Round($size/1MB,2)} } | Sort-Object SizeMB -Descending | Select-Object -First 10",
        "explanation": "Scans each top-level folder and calculates total size of all contained files"
    },
    {
        "instruction": "Report top 5 largest directories with sizes",
        "command": "$folders = Get-ChildItem -Path C:\\ -Directory -ErrorAction SilentlyContinue; foreach ($f in $folders) { $bytes = (Get-ChildItem -Path $f.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; [PSCustomObject]@{Name=$f.Name; SizeGB=[math]::Round($bytes/1GB,2)} } | Sort-Object SizeGB -Descending | Select-Object -First 5",
        "explanation": "Full directory size analysis with GB output - directories have no inherent size, must calculate from files"
    },
    {
        "instruction": "Disk space analysis by folder",
        "command": "Get-ChildItem C:\\ -Directory | Select-Object Name, @{N='SizeGB';E={[math]::Round((Get-ChildItem $_.FullName -Recurse -File -EA 0 | Measure-Object Length -Sum).Sum/1GB,2)}} | Sort-Object SizeGB -Descending",
        "explanation": "Uses calculated property to get folder sizes. Note: Get-ChildItem -Directory returns folders but they don't have Length"
    },
]

ADVANCED_POWERSHELL_TASKS = [
    {
        "instruction": "Monitor a log file in real-time",
        "command": "Get-Content -Path 'C:\\Logs\\app.log' -Wait -Tail 50",
        "explanation": "Tails log file like Unix tail -f"
    },
    {
        "instruction": "Find and kill process using port 8080",
        "command": "$proc = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -First 1; if($proc) { Stop-Process -Id $proc.OwningProcess -Force; 'Killed process ' + $proc.OwningProcess } else { 'No process on port 8080' }",
        "explanation": "Finds process using port 8080 and terminates it"
    },
    {
        "instruction": "Create a scheduled task to run a script daily",
        "command": "$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument '-NoProfile -File C:\\Scripts\\backup.ps1'\n$trigger = New-ScheduledTaskTrigger -Daily -At 3am\nRegister-ScheduledTask -TaskName 'DailyBackup' -Action $action -Trigger $trigger -RunLevel Highest",
        "explanation": "Creates a scheduled task running PowerShell script at 3 AM daily"
    },
    {
        "instruction": "Export Windows Event Logs for the last 24 hours",
        "command": "$yesterday = (Get-Date).AddDays(-1)\nGet-WinEvent -FilterHashtable @{LogName='Application','System'; StartTime=$yesterday} | Export-Csv -Path 'EventLogs.csv' -NoTypeInformation",
        "explanation": "Exports Application and System event logs from last 24 hours"
    },
    {
        "instruction": "Find all failed login attempts",
        "command": "Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 100 | Select-Object TimeCreated, @{N='Account';E={$_.Properties[5].Value}}, @{N='SourceIP';E={$_.Properties[19].Value}}",
        "explanation": "Lists failed login attempts from Security event log (Event ID 4625)"
    },
    {
        "instruction": "Remotely restart a service on multiple servers",
        "command": "$servers = 'Server1','Server2','Server3'\nInvoke-Command -ComputerName $servers -ScriptBlock { Restart-Service -Name 'Spooler' -Force }",
        "explanation": "Uses PowerShell remoting to restart Print Spooler on multiple servers"
    },
    {
        "instruction": "Check certificate expiration dates",
        "command": "Get-ChildItem -Path Cert:\\LocalMachine\\My | Where-Object {$_.NotAfter -lt (Get-Date).AddDays(30)} | Select-Object Subject, NotAfter, Thumbprint",
        "explanation": "Lists certificates expiring within 30 days"
    },
    {
        "instruction": "Create a new local admin user",
        "command": "$password = ConvertTo-SecureString 'TempP@ssw0rd!' -AsPlainText -Force\nNew-LocalUser -Name 'AdminUser' -Password $password -FullName 'Admin User' -Description 'Temporary admin'\nAdd-LocalGroupMember -Group 'Administrators' -Member 'AdminUser'",
        "explanation": "Creates local user and adds to Administrators group"
    },
    {
        "instruction": "Monitor CPU and memory usage continuously",
        "command": "while($true) { $cpu = (Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples.CookedValue; $mem = (Get-Counter '\\Memory\\% Committed Bytes In Use').CounterSamples.CookedValue; Write-Host (Get-Date -Format 'HH:mm:ss') \"CPU: $([math]::Round($cpu,1))% MEM: $([math]::Round($mem,1))%\"; Start-Sleep 2 }",
        "explanation": "Monitors system resources in real-time"
    },
    {
        "instruction": "Compress and archive old log files",
        "command": "$cutoff = (Get-Date).AddDays(-7)\nGet-ChildItem -Path 'C:\\Logs' -Filter '*.log' | Where-Object {$_.LastWriteTime -lt $cutoff} | Compress-Archive -DestinationPath \"C:\\Archive\\Logs_$(Get-Date -Format 'yyyyMMdd').zip\"\nGet-ChildItem -Path 'C:\\Logs' -Filter '*.log' | Where-Object {$_.LastWriteTime -lt $cutoff} | Remove-Item",
        "explanation": "Archives logs older than 7 days and removes originals"
    },
    {
        "instruction": "Check for pending reboot",
        "command": "$rebootPending = Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending'\n$rebootRequired = Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired'\nif($rebootPending -or $rebootRequired) { 'REBOOT REQUIRED' } else { 'No reboot pending' }",
        "explanation": "Checks registry keys indicating pending reboot"
    },
    {
        "instruction": "Get BIOS and hardware information",
        "command": "Get-CimInstance -ClassName Win32_BIOS | Format-List *\nGet-CimInstance -ClassName Win32_ComputerSystem | Select-Object Manufacturer, Model, TotalPhysicalMemory, NumberOfProcessors",
        "explanation": "Retrieves BIOS version and hardware details"
    },
    {
        "instruction": "Find duplicate files by hash",
        "command": "Get-ChildItem -Path 'C:\\Data' -Recurse -File | Get-FileHash | Group-Object Hash | Where-Object {$_.Count -gt 1} | ForEach-Object {$_.Group}",
        "explanation": "Identifies duplicate files using SHA256 hash comparison"
    },
    {
        "instruction": "Run command on remote computer",
        "command": "Invoke-Command -ComputerName 'Server01' -ScriptBlock { Get-Service | Where Status -eq 'Running' } -Credential (Get-Credential)",
        "explanation": "Executes PowerShell on remote machine via WinRM"
    },
    {
        "instruction": "Create PSCredential object securely",
        "command": "$username = 'domain\\admin'\n$password = Read-Host 'Password' -AsSecureString\n$cred = New-Object System.Management.Automation.PSCredential($username, $password)",
        "explanation": "Creates credential object for authentication without plain text"
    },
    {
        "instruction": "Export data to JSON file",
        "command": "Get-Process | Select-Object Name, Id, CPU, WorkingSet64 | ConvertTo-Json | Out-File 'processes.json'",
        "explanation": "Exports object data as formatted JSON"
    },
    {
        "instruction": "Import data from JSON file",
        "command": "$data = Get-Content 'config.json' | ConvertFrom-Json\n$data.settings.timeout",
        "explanation": "Reads JSON file and accesses nested properties"
    },
    {
        "instruction": "Export data to CSV file",
        "command": "Get-Process | Select-Object Name, Id, CPU | Export-Csv -Path 'processes.csv' -NoTypeInformation",
        "explanation": "Exports to CSV without type header row"
    },
    {
        "instruction": "Parse CSV file",
        "command": "$users = Import-Csv -Path 'users.csv'\n$users | Where-Object {$_.Department -eq 'IT'}",
        "explanation": "Imports CSV and filters by column value"
    },
    {
        "instruction": "Work with XML data",
        "command": "[xml]$config = Get-Content 'app.config'\n$config.configuration.appSettings.add | Where-Object {$_.key -eq 'ConnectionString'}",
        "explanation": "Parses XML file and queries elements"
    },
    {
        "instruction": "Send email notification",
        "command": "Send-MailMessage -From 'alerts@company.com' -To 'admin@company.com' -Subject 'Server Alert' -Body 'Disk space low' -SmtpServer 'smtp.company.com'",
        "explanation": "Sends email via SMTP server"
    },
    {
        "instruction": "Create a background job",
        "command": "$job = Start-Job -ScriptBlock { Get-ChildItem C:\\ -Recurse }\nWait-Job $job\nReceive-Job $job",
        "explanation": "Runs long-running task in background"
    },
    {
        "instruction": "Run multiple jobs in parallel",
        "command": "$servers = 'srv1','srv2','srv3'\n$jobs = $servers | ForEach-Object { Start-Job -ScriptBlock {param($s) Test-Connection $s -Count 1} -ArgumentList $_ }\n$jobs | Wait-Job | Receive-Job",
        "explanation": "Parallel execution across multiple targets"
    },
    {
        "instruction": "Use PowerShell 7 parallel foreach",
        "command": "1..10 | ForEach-Object -Parallel { Start-Sleep 1; \"Processed $_\" } -ThrottleLimit 5",
        "explanation": "Parallel processing with throttle control (PowerShell 7+)"
    },
    {
        "instruction": "Create a hash table / dictionary",
        "command": "$config = @{\n    Server = 'localhost'\n    Port = 5432\n    Database = 'mydb'\n}\n$config.Server",
        "explanation": "Creates key-value dictionary structure"
    },
    {
        "instruction": "Work with arrays",
        "command": "$arr = @(1, 2, 3, 4, 5)\n$arr += 6\n$arr | Where-Object {$_ -gt 3}",
        "explanation": "Array manipulation and filtering"
    },
    {
        "instruction": "Define a custom function",
        "command": "function Get-DiskSpaceReport {\n    param([string]$ComputerName = $env:COMPUTERNAME)\n    Get-CimInstance -ClassName Win32_LogicalDisk -ComputerName $ComputerName |\n    Where-Object {$_.DriveType -eq 3} |\n    Select-Object DeviceID, @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,2)}}\n}",
        "explanation": "Creates reusable function with parameters"
    },
    {
        "instruction": "Use try-catch for error handling",
        "command": "try {\n    $result = Get-Content 'nonexistent.txt' -ErrorAction Stop\n} catch [System.IO.FileNotFoundException] {\n    Write-Warning 'File not found'\n} catch {\n    Write-Error $_.Exception.Message\n}",
        "explanation": "Structured error handling with specific exception types"
    },
    {
        "instruction": "Create custom PSObject",
        "command": "$server = [PSCustomObject]@{\n    Name = 'WebServer01'\n    IP = '192.168.1.10'\n    Status = 'Online'\n    LastCheck = Get-Date\n}\n$server",
        "explanation": "Creates structured object with named properties"
    },
    {
        "instruction": "Filter objects with Where-Object",
        "command": "Get-Service | Where-Object {$_.Status -eq 'Running' -and $_.StartType -eq 'Automatic'}",
        "explanation": "Complex filtering with multiple conditions"
    },
    {
        "instruction": "Transform objects with Select-Object",
        "command": "Get-Process | Select-Object Name, @{N='MemoryMB';E={[math]::Round($_.WorkingSet64/1MB)}}, @{N='CPUSeconds';E={[math]::Round($_.CPU,2)}}",
        "explanation": "Creates calculated properties during selection"
    },
    {
        "instruction": "Group and aggregate data",
        "command": "Get-WinEvent -LogName System -MaxEvents 1000 | Group-Object ProviderName | Sort-Object Count -Descending | Select-Object -First 10 Name, Count",
        "explanation": "Groups events by source and counts occurrences"
    },
    {
        "instruction": "Measure object statistics",
        "command": "Get-ChildItem -Path 'C:\\Data' -Recurse -File | Measure-Object -Property Length -Sum -Average -Maximum -Minimum",
        "explanation": "Calculates statistics on numeric properties"
    },
    {
        "instruction": "Format output as table",
        "command": "Get-Process | Format-Table Name, Id, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet64/1MB)};Align='Right'} -AutoSize",
        "explanation": "Custom table formatting with alignment"
    },
    {
        "instruction": "Sort objects by multiple properties",
        "command": "Get-ChildItem | Sort-Object @{E='PSIsContainer';Descending=$true}, Name",
        "explanation": "Sorts directories first, then files by name"
    },
    {
        "instruction": "Use regular expressions",
        "command": "$text = 'Email: user@example.com'\nif($text -match '([\\w.-]+)@([\\w.-]+)') { $matches[1] }",
        "explanation": "Regex matching with capture groups"
    },
    {
        "instruction": "Replace text with regex",
        "command": "$content = Get-Content 'file.txt' -Raw\n$content -replace '(?i)password\\s*=\\s*\"[^\"]+\"', 'password=\"REDACTED\"'",
        "explanation": "Case-insensitive regex replacement"
    },
    {
        "instruction": "Split and join strings",
        "command": "$path = 'C:\\Users\\John\\Documents'\n$parts = $path -split '\\\\'\n$parts[-1]  # Gets 'Documents'",
        "explanation": "String splitting and array indexing"
    },
    {
        "instruction": "Get ACL (permissions) of a file",
        "command": "Get-Acl -Path 'C:\\Sensitive\\data.txt' | Format-List",
        "explanation": "Shows file owner and access control entries"
    },
    {
        "instruction": "Set file permissions",
        "command": "$acl = Get-Acl 'C:\\Folder'\n$rule = New-Object System.Security.AccessControl.FileSystemAccessRule('Users','Read','Allow')\n$acl.AddAccessRule($rule)\nSet-Acl -Path 'C:\\Folder' -AclObject $acl",
        "explanation": "Adds read permission for Users group"
    },
    {
        "instruction": "Get Active Directory user info",
        "command": "Get-ADUser -Identity 'jsmith' -Properties * | Select-Object Name, EmailAddress, Department, LastLogonDate",
        "explanation": "Retrieves AD user details (requires RSAT)"
    },
    {
        "instruction": "Query Active Directory computers",
        "command": "Get-ADComputer -Filter {OperatingSystem -like '*Server*'} -Properties OperatingSystem, LastLogonTimestamp | Select-Object Name, OperatingSystem",
        "explanation": "Finds all Windows Server machines in AD"
    },
    {
        "instruction": "Get installed hotfixes",
        "command": "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10 HotFixID, InstalledOn, Description",
        "explanation": "Lists recently installed Windows updates"
    },
    {
        "instruction": "Check disk health with SMART data",
        "command": "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, HealthStatus, OperationalStatus, Size",
        "explanation": "Shows physical disk health status"
    },
    {
        "instruction": "Get USB devices",
        "command": "Get-PnpDevice -Class USB | Where-Object Status -eq 'OK' | Select-Object FriendlyName, Status",
        "explanation": "Lists connected USB devices"
    },
    {
        "instruction": "Monitor file system changes",
        "command": "$watcher = New-Object System.IO.FileSystemWatcher\n$watcher.Path = 'C:\\Watched'\n$watcher.EnableRaisingEvents = $true\nRegister-ObjectEvent $watcher 'Created' -Action { Write-Host \"Created: $($Event.SourceEventArgs.FullPath)\" }",
        "explanation": "Sets up file system watcher for change notifications"
    },
    {
        "instruction": "Create Windows event log entry",
        "command": "Write-EventLog -LogName Application -Source 'MyScript' -EventId 1001 -EntryType Information -Message 'Script completed successfully'",
        "explanation": "Writes custom entry to Windows Event Log"
    },
    {
        "instruction": "Get network connection statistics",
        "command": "Get-NetTCPConnection | Group-Object State | Select-Object Name, Count",
        "explanation": "Summarizes TCP connections by state"
    },
    {
        "instruction": "Test website availability",
        "command": "try { $response = Invoke-WebRequest -Uri 'https://example.com' -TimeoutSec 10; \"Status: $($response.StatusCode)\" } catch { \"Failed: $_\" }",
        "explanation": "HTTP health check with error handling"
    },
    {
        "instruction": "Generate HTML report",
        "command": "Get-Process | Select-Object Name, CPU, WorkingSet64 | ConvertTo-Html -Title 'Process Report' -PreContent '<h1>Running Processes</h1>' | Out-File 'report.html'",
        "explanation": "Creates formatted HTML report from data"
    },
    {
        "instruction": "Sign a PowerShell script",
        "command": "$cert = Get-ChildItem Cert:\\CurrentUser\\My -CodeSigningCert | Select-Object -First 1\nSet-AuthenticodeSignature -FilePath 'script.ps1' -Certificate $cert",
        "explanation": "Digitally signs script with code signing certificate"
    },
    {
        "instruction": "Encrypt a file",
        "command": "$secureString = ConvertTo-SecureString 'MyPassword' -AsPlainText -Force\n$encrypted = ConvertFrom-SecureString $secureString\n$encrypted | Out-File 'encrypted.txt'",
        "explanation": "Encrypts sensitive data using DPAPI"
    },
    {
        "instruction": "Profile script performance",
        "command": "Measure-Command { Get-ChildItem C:\\ -Recurse -ErrorAction SilentlyContinue | Out-Null }",
        "explanation": "Measures execution time of script block"
    },
]

SERVICE_MANAGEMENT_TASKS = [
    {
        "instruction": "List all services and their status",
        "command": "Get-Service | Select-Object Name, DisplayName, Status, StartType | Sort-Object Status, Name",
        "explanation": "Lists all Windows services with current status"
    },
    {
        "instruction": "Start a stopped service",
        "command": "Start-Service -Name 'wuauserv' -PassThru",
        "explanation": "Starts Windows Update service"
    },
    {
        "instruction": "Stop a service gracefully",
        "command": "Stop-Service -Name 'Spooler' -Force -PassThru",
        "explanation": "Stops Print Spooler service"
    },
    {
        "instruction": "Set service to start automatically",
        "command": "Set-Service -Name 'wuauserv' -StartupType Automatic",
        "explanation": "Configures Windows Update service to start automatically"
    },
    {
        "instruction": "Find services that failed to start",
        "command": "Get-WinEvent -FilterHashtable @{LogName='System'; Id=7000,7001,7022,7023,7024} -MaxEvents 50 | Select-Object TimeCreated, Message",
        "explanation": "Finds service control manager errors"
    },
    {
        "instruction": "Restart IIS without downtime",
        "command": "iisreset /restart",
        "explanation": "Restarts IIS web server"
    },
    {
        "instruction": "Check if a service is running and start if not",
        "command": "$svc = Get-Service -Name 'MSSQLSERVER' -ErrorAction SilentlyContinue; if($svc.Status -ne 'Running') { Start-Service $svc -PassThru } else { 'Service already running' }",
        "explanation": "Conditional service start"
    },
]

# =============================================================================
# REGISTRY OPERATIONS
# =============================================================================

REGISTRY_TASKS = [
    {
        "instruction": "Read a registry value",
        "command": "Get-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' -Name 'ProductName'",
        "explanation": "Reads Windows product name from registry"
    },
    {
        "instruction": "Create a new registry key",
        "command": "New-Item -Path 'HKLM:\\SOFTWARE\\MyCompany' -Force",
        "explanation": "Creates new registry key"
    },
    {
        "instruction": "Set a registry value",
        "command": "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\MyCompany' -Name 'AppVersion' -Value '1.0.0'",
        "explanation": "Creates or updates a registry value"
    },
    {
        "instruction": "Export registry key to file",
        "command": "reg export 'HKLM\\SOFTWARE\\MyCompany' 'C:\\Backup\\MyCompany.reg' /y",
        "explanation": "Exports registry key to .reg file for backup"
    },
    {
        "instruction": "Disable Windows telemetry via registry",
        "command": "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection' -Name 'AllowTelemetry' -Value 0 -Type DWord",
        "explanation": "Disables Windows telemetry through group policy registry"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up a new Windows development environment",
        "steps": [
            "Install Windows Package Manager (winget) if not present",
            "Install Git: winget install Git.Git",
            "Install VS Code: winget install Microsoft.VisualStudioCode",
            "Install Node.js LTS: winget install OpenJS.NodeJS.LTS",
            "Install Python: winget install Python.Python.3.11",
            "Configure Git global settings (name, email)",
            "Set up SSH keys for Git authentication",
            "Install Windows Terminal: winget install Microsoft.WindowsTerminal",
            "Configure PowerShell profile with aliases and functions"
        ]
    },
    {
        "instruction": "Troubleshoot slow Windows boot time",
        "steps": [
            "Check startup programs: Get-CimInstance Win32_StartupCommand",
            "Review startup impact in Task Manager",
            "Check for pending Windows updates",
            "Analyze boot trace: xbootmgr -trace boot",
            "Review System event log for errors during boot",
            "Check disk health with CrystalDiskInfo or SMART data",
            "Disable unnecessary startup services",
            "Consider fast startup settings in Power Options"
        ]
    },
    {
        "instruction": "Harden Windows security for a workstation",
        "steps": [
            "Enable BitLocker drive encryption",
            "Configure Windows Firewall rules",
            "Enable Windows Defender with cloud protection",
            "Disable unnecessary services (Telnet, FTP)",
            "Configure account lockout policies",
            "Enable audit logging for security events",
            "Disable SMBv1: Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol",
            "Configure Windows Update for automatic security updates",
            "Review and restrict local admin accounts"
        ]
    },
    {
        "instruction": "Migrate user profile to new computer",
        "steps": [
            "Document installed applications on source machine",
            "Export browser bookmarks and settings",
            "Backup user folders (Documents, Desktop, Downloads, Pictures)",
            "Export Outlook profile and data files",
            "Export credential manager entries if needed",
            "Copy AppData folders for critical applications",
            "On target: Create user account with same settings",
            "Restore data to appropriate locations",
            "Reinstall required applications",
            "Verify file associations and default programs"
        ]
    },
    {
        "instruction": "Set up Windows Server as a file server",
        "steps": [
            "Install File Server role via Server Manager",
            "Configure storage spaces or RAID for data drives",
            "Create folder structure for shares",
            "Set up NTFS permissions on folders",
            "Create SMB shares with appropriate permissions",
            "Enable access-based enumeration (ABE)",
            "Configure shadow copies for recovery",
            "Set up quotas if needed",
            "Configure backup solution (Windows Server Backup)",
            "Document share paths and permissions"
        ]
    },
    {
        "instruction": "Diagnose and fix Windows Update failures",
        "steps": [
            "Check Windows Update log: Get-WindowsUpdateLog",
            "Run Windows Update troubleshooter",
            "Check disk space on system drive",
            "Stop Windows Update services: Stop-Service wuauserv, bits",
            "Clear update cache: Remove-Item C:\\Windows\\SoftwareDistribution\\* -Recurse",
            "Restart services: Start-Service wuauserv, bits",
            "Run SFC: sfc /scannow",
            "Run DISM: DISM /Online /Cleanup-Image /RestoreHealth",
            "Retry Windows Update"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is the difference between PowerShell and CMD?",
        "answer": "PowerShell is an object-oriented shell built on .NET, while CMD is a legacy text-based shell. Key differences: 1) PowerShell passes objects between commands (not just text), 2) PowerShell has cmdlets with Verb-Noun naming (Get-Process vs tasklist), 3) PowerShell supports .NET types, methods, and properties, 4) PowerShell has a rich scripting language with functions, classes, and modules, 5) PowerShell has built-in remoting capabilities. CMD is simpler but limited to text parsing."
    },
    {
        "question": "What is the Windows Registry?",
        "answer": "The Windows Registry is a hierarchical database storing system and application configuration. It has five root keys: HKEY_CLASSES_ROOT (file associations), HKEY_CURRENT_USER (current user settings), HKEY_LOCAL_MACHINE (system-wide settings), HKEY_USERS (all user profiles), HKEY_CURRENT_CONFIG (hardware profile). Values can be strings, numbers, or binary data. Changes typically require restart. Always backup before editing - incorrect changes can break Windows."
    },
    {
        "question": "What are Windows Services?",
        "answer": "Windows Services are long-running background processes that start automatically (or on trigger). They run without user interaction, often under SYSTEM or service accounts. Services can be controlled via services.msc, PowerShell (Get-Service), or sc.exe. Startup types: Automatic (starts at boot), Manual (starts on demand), Disabled. Examples: Windows Update (wuauserv), Print Spooler, SQL Server."
    },
    {
        "question": "What is UAC (User Account Control)?",
        "answer": "UAC is a Windows security feature that prevents unauthorized changes to the OS. When a program needs admin rights, UAC prompts for consent or credentials. It implements least-privilege by running most apps without admin rights. UAC has levels from Always Notify to Never Notify. Even admin accounts run with standard privileges until elevation is granted. Disabling UAC reduces security significantly."
    },
    {
        "question": "What is the difference between 32-bit and 64-bit Windows?",
        "answer": "64-bit Windows can address more than 4GB RAM (up to 128GB+ depending on edition), run 64-bit applications natively, and provides better security features like larger address space randomization. 32-bit apps run in WoW64 compatibility layer. System32 contains 64-bit DLLs, SysWOW64 contains 32-bit DLLs (confusingly named). Program Files vs Program Files (x86) separates architectures."
    },
    {
        "question": "What is NTFS and why does it matter?",
        "answer": "NTFS (New Technology File System) is Windows' primary file system. Features: file/folder permissions (ACLs), encryption (EFS), compression, disk quotas, shadow copies, journaling for crash recovery, support for large files and volumes. Compared to FAT32: no 4GB file limit, better security, more resilient to corruption. ExFAT is simpler and cross-platform but lacks NTFS security features."
    },
]

# =============================================================================
# WINDOWS DNS, DHCP, AND NETWORKING
# =============================================================================

DNS_DHCP_NETWORKING = [
    {
        "question": "How do I configure Windows DNS Server?",
        "answer": "Windows DNS Server is an AD-integrated DNS role. Install: Add-WindowsFeature DNS -IncludeManagementTools. Key zones: Forward lookup (name→IP), Reverse lookup (IP→name). Zone types: Primary (read/write), Secondary (read-only copy), Stub (NS records only), AD-integrated (replicated via AD). Create zone: Add-DnsServerPrimaryZone -Name 'domain.local' -ZoneFile 'domain.local.dns'. Records: A (host), AAAA (IPv6), CNAME (alias), MX (mail), SRV (services), PTR (reverse). dnscmd or PowerShell DNS cmdlets for management."
    },
    {
        "question": "What is Active Directory-integrated DNS and why use it?",
        "answer": "AD-integrated DNS stores zones in Active Directory instead of zone files. Benefits: 1) Multi-master replication (any DC can write), 2) Secure dynamic updates (only authenticated computers), 3) Replication uses AD topology (no separate zone transfers), 4) Integrated with AD backup. Enable: Set-DnsServerPrimaryZone -Name 'domain.local' -ReplicationScope Domain. Scopes: Forest (all DCs), Domain (domain DCs only), Legacy (pre-2003 compatibility). Requires DNS on domain controllers. Best practice for AD environments."
    },
    {
        "question": "How do I troubleshoot DNS resolution issues?",
        "answer": "Troubleshooting steps: 1) nslookup <hostname> - test DNS resolution. 2) ipconfig /displaydns - check DNS cache. 3) ipconfig /flushdns - clear cache. 4) Resolve-DnsName <hostname> -Server <dnsserver> - test specific server. 5) Check DNS server settings: Get-DnsClientServerAddress. 6) Test DNS server: Test-DnsServer -IPAddress <ip>. Common issues: wrong DNS servers configured, DNS server not responding, missing records, stale records, forwarder issues. Event logs: DNS Server, System. Tools: DCDiag /test:DNS, DNSLint."
    },
    {
        "question": "How do I configure conditional DNS forwarding?",
        "answer": "Conditional forwarders route queries for specific domains to designated DNS servers. Use for: partner domains, hybrid cloud, forest trusts. Create: Add-DnsServerConditionalForwarderZone -Name 'partner.com' -MasterServers 10.0.0.1,10.0.0.2. Remove: Remove-DnsServerZone -Name 'partner.com' -Force. View: Get-DnsServerZone | Where ZoneType -eq 'Forwarder'. AD-integrated conditional forwarders replicate to other DCs. Alternative: stub zones (only NS records, less manual maintenance). For Azure: forward to 168.63.129.16 for Azure Private DNS."
    },
    {
        "question": "How do I set up Windows DHCP Server?",
        "answer": "DHCP Server provides automatic IP configuration. Install: Add-WindowsFeature DHCP -IncludeManagementTools. Authorize in AD: Add-DhcpServerInDC -DnsName 'dhcp.domain.local'. Create scope: Add-DhcpServerv4Scope -Name 'MainLAN' -StartRange 192.168.1.100 -EndRange 192.168.1.200 -SubnetMask 255.255.255.0. Set options: Set-DhcpServerv4OptionValue -Router 192.168.1.1 -DnsServer 192.168.1.10. Reservations: Add-DhcpServerv4Reservation -ScopeId 192.168.1.0 -IPAddress 192.168.1.50 -ClientId 'aa-bb-cc-dd-ee-ff'. Activate: Set-DhcpServerv4Scope -ScopeId 192.168.1.0 -State Active."
    },
    {
        "question": "How does DHCP failover work in Windows Server?",
        "answer": "DHCP failover provides high availability. Modes: 1) Load Balance (both servers active, split leases), 2) Hot Standby (primary active, secondary standby). Configure: Add-DhcpServerv4Failover -Name 'DHCPFailover' -PartnerServer 'DHCP2' -ScopeId 192.168.1.0 -LoadBalancePercent 50. Hot standby: Add-DhcpServerv4Failover -Mode HotStandby -ReservePercent 10. State synchronization automatic. MCLT (Maximum Client Lead Time) controls lease extension. Replication: Invoke-DhcpServerv4FailoverReplication. No third-party clustering needed. Works across subnets with IP helpers."
    },
    {
        "question": "How do I configure DHCP options and classes?",
        "answer": "DHCP options provide additional configuration to clients. Server-level: Set-DhcpServerv4OptionValue -DnsDomain 'domain.local'. Scope-level: Set-DhcpServerv4OptionValue -ScopeId 192.168.1.0 -Router 192.168.1.1. Common options: 003 (Router), 006 (DNS), 015 (Domain Name), 044 (WINS), 066/067 (PXE Boot). Vendor classes: target specific vendors. User classes: target client types. Policy-based assignment: Set-DhcpServerv4Policy -Name 'Phones' -Condition 'OR' -VendorClass 'Cisco*'. View options: Get-DhcpServerv4OptionDefinition."
    },
    {
        "question": "How do I configure Windows Firewall with Advanced Security?",
        "answer": "Windows Firewall filters network traffic by rules. Profiles: Domain (AD network), Private (trusted), Public (untrusted). Manage: wf.msc GUI, netsh advfirewall, PowerShell NetSecurity module. Create rule: New-NetFirewallRule -DisplayName 'Allow SSH' -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow. Disable: Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled False. View: Get-NetFirewallRule | Where Enabled -eq True. Export: netsh advfirewall export 'c:\\firewall.wfw'. GPO: Computer Config > Policies > Windows Settings > Security Settings > Windows Firewall."
    },
    {
        "question": "How does Network Location Awareness (NLA) work?",
        "answer": "NLA detects network type to apply correct firewall profile. Detection: 1) Domain: can reach DC (via LDAP), 2) Private: user selected trusted network, 3) Public: default/untrusted. Service: Network Location Awareness (NlaSvc). Troubleshooting: nltest /dsgetdc:domain.local, Get-NetConnectionProfile. Change profile: Set-NetConnectionProfile -InterfaceIndex 12 -NetworkCategory Private. Stuck on Public: restart NLA service, check DC connectivity, verify DNS. GPO: Computer Config > Policies > Network List Manager Policies. Network requiring authentication defaults to Public until authenticated."
    },
    {
        "question": "How do I configure network teaming (NIC Teaming) in Windows?",
        "answer": "NIC Teaming (LBFO) bonds multiple NICs for redundancy/bandwidth. Create: New-NetLbfoTeam -Name 'Team1' -TeamMembers 'Ethernet1','Ethernet2' -TeamingMode SwitchIndependent -LoadBalancingAlgorithm Dynamic. Modes: Static (requires switch config), Switch Independent (no switch config), LACP (802.3ad). Load balancing: Address Hash, Hyper-V Port, Dynamic. Add VLAN: Add-NetLbfoTeamNic -Team 'Team1' -VlanId 100. View: Get-NetLbfoTeam. Note: In Azure/Hyper-V, use virtual switch teaming or Azure Load Balancer instead. Windows Server 2022: Switch Embedded Teaming (SET) preferred for Hyper-V."
    },
    {
        "question": "How do I troubleshoot Windows networking with PowerShell?",
        "answer": "Key cmdlets: Test-NetConnection <host> -Port 443 (telnet replacement). Get-NetIPConfiguration (ipconfig equivalent). Get-NetRoute (routing table). Test-Connection <host> -Count 4 (ping). Get-NetTCPConnection (netstat). Get-NetNeighbor (ARP table). Resolve-DnsName <host>. tracert: Test-NetConnection -TraceRoute. Port scan: Test-NetConnection -Port 80,443,3389. Advanced: Get-NetAdapter | Get-NetAdapterStatistics. Clear ARP: Remove-NetNeighbor -Confirm:$false. Reset stack: netsh winsock reset, netsh int ip reset."
    },
]

# =============================================================================
# ACTIVE DIRECTORY ADMINISTRATION
# =============================================================================

ACTIVE_DIRECTORY = [
    {
        "question": "What is Active Directory and how is it structured?",
        "answer": "Active Directory (AD) is a directory service for Windows networks. Logical structure: Forest (security boundary) > Domains (admin boundary) > OUs (organizational units for delegation/GPO). Physical: Sites (network topology) > Domain Controllers (host AD). Objects: Users, Computers, Groups, OUs. Database: NTDS.dit. Protocol: LDAP (389/636 for secure). Key services: DNS (name resolution), Kerberos (authentication), LDAP (directory queries). Global Catalog (GC): partial replica of all objects in forest on port 3268/3269."
    },
    {
        "question": "How do I install and promote a Domain Controller?",
        "answer": "Install AD DS role: Install-WindowsFeature AD-Domain-Services -IncludeManagementTools. New forest: Install-ADDSForest -DomainName 'domain.local' -DomainNetbiosName 'DOMAIN' -ForestMode WinThreshold -DomainMode WinThreshold. Additional DC: Install-ADDSDomainController -DomainName 'domain.local' -Credential (Get-Credential). RODC: -ReadOnlyReplica. Prerequisites: static IP, DNS pointing to existing DC (or self for first), local admin rights. Verify: dcdiag, repadmin /replsummary. DSRM password required for DC recovery."
    },
    {
        "question": "How does Active Directory replication work?",
        "answer": "AD uses multi-master replication - any DC can write changes. Intrasite: automatic, immediate (15-second notification). Intersite: scheduled, compressed. Replication topology: KCC (Knowledge Consistency Checker) auto-generates. Objects: repadmin /showrepl, repadmin /replsummary. Force sync: repadmin /syncall /AeD. Conflicts: last-writer-wins using version numbers + timestamps. USN (Update Sequence Number) tracks changes. Lingering objects: repadmin /removelingeringobjects. SYSVOL replication: DFSR (2008+) or FRS (legacy). Monitor: AD Replication Status Tool."
    },
    {
        "question": "What are FSMO roles and how do I manage them?",
        "answer": "FSMO (Flexible Single Master Operations) - 5 roles for operations requiring single authority. Forest-wide: Schema Master (schema changes), Domain Naming Master (add/remove domains). Domain-wide: PDC Emulator (time source, password changes, GPO), RID Master (issues RID pools for SIDs), Infrastructure Master (cross-domain references). View: netdom query fsmo. Transfer: Move-ADDirectoryServerOperationMasterRole -Identity 'DC2' -OperationMasterRole PDCEmulator. Seize (if source offline): -Force parameter. PDC Emulator most critical - users notice immediately if offline."
    },
    {
        "question": "How do I create and manage AD users with PowerShell?",
        "answer": "Create user: New-ADUser -Name 'John Smith' -SamAccountName 'jsmith' -UserPrincipalName 'jsmith@domain.local' -Path 'OU=Users,DC=domain,DC=local' -AccountPassword (ConvertTo-SecureString 'P@ssw0rd' -AsPlainText -Force) -Enabled $true. Bulk create from CSV: Import-Csv users.csv | ForEach { New-ADUser @params }. Modify: Set-ADUser jsmith -Description 'IT Department'. Disable: Disable-ADAccount jsmith. Reset password: Set-ADAccountPassword -Identity jsmith -Reset -NewPassword (ConvertTo-SecureString 'NewP@ss' -AsPlainText -Force). Delete: Remove-ADUser jsmith. Search: Get-ADUser -Filter {Department -eq 'IT'}."
    },
    {
        "question": "How do AD groups work and what are the best practices?",
        "answer": "Group scopes: Domain Local (assign permissions), Global (organize users), Universal (forest-wide). Types: Security (permissions) vs Distribution (email). AGDLP strategy: Accounts → Global groups → Domain Local groups → Permissions. Example: User jsmith → G_IT_Staff (global) → DL_FileShare_Read (domain local) → NTFS permission. Create: New-ADGroup -Name 'G_IT_Staff' -GroupScope Global -GroupCategory Security -Path 'OU=Groups,DC=domain,DC=local'. Add member: Add-ADGroupMember -Identity 'G_IT_Staff' -Members 'jsmith'. Nested groups: Add-ADGroupMember -Identity 'DL_FileShare_Read' -Members 'G_IT_Staff'."
    },
    {
        "question": "How do I configure Group Policy Objects (GPOs)?",
        "answer": "GPOs apply settings to users/computers. Create: New-GPO -Name 'Desktop Settings'. Link: New-GPLink -Name 'Desktop Settings' -Target 'OU=Workstations,DC=domain,DC=local'. Edit: gpmc.msc or Set-GPRegistryValue. Processing order: Local, Site, Domain, OU (last wins). Block inheritance: Set-GPInheritance -Target 'OU=Servers,DC=domain,DC=local' -IsBlocked Yes. Enforce: Set-GPLink -Name 'Security Policy' -Enforced Yes. Results: gpresult /r (local), Get-GPResultantSetOfPolicy. Refresh: gpupdate /force. Backup: Backup-GPO -All -Path 'C:\\GPOBackup'. Model: Get-GPOReport -Name 'Policy' -ReportType HTML."
    },
    {
        "question": "How do I configure AD Sites and Services for replication?",
        "answer": "Sites model physical network topology. Create site: New-ADReplicationSite -Name 'Branch-Office'. Create subnet: New-ADReplicationSubnet -Name '192.168.2.0/24' -Site 'Branch-Office'. Site links control replication: New-ADReplicationSiteLink -Name 'HQ-Branch' -SitesIncluded 'HQ','Branch-Office' -Cost 100 -ReplicationFrequencyInMinutes 180. Move DC to site: Move-ADDirectoryServer -Identity 'DC2' -Site 'Branch-Office'. Bridgehead servers: Set-ADReplicationSiteLinkBridge. View: Get-ADReplicationSite, Get-ADReplicationSiteLink. KCC recalculates topology every 15 minutes."
    },
    {
        "question": "How do I create and manage AD trusts?",
        "answer": "Trusts allow authentication across domains/forests. Types: Parent-Child (automatic, two-way), Tree-Root (automatic, two-way), Forest (manual, can be one or two-way), External (to non-forest domain, one-way), Shortcut (optimize auth in forest). Create forest trust: netdom trust <domain1> /d:<domain2> /add /twoway /forest. PowerShell: New-ADTrust. Verify: netdom trust <domain> /verify. Selective auth: limit which users can authenticate. SID filtering: enabled by default, prevents SID history attacks. Troubleshoot: nltest /sc_query:<domain>, klist."
    },
    {
        "question": "How do I troubleshoot Active Directory issues?",
        "answer": "Key tools: dcdiag (comprehensive DC health), repadmin (replication status), nltest (secure channel, DC location). Authentication: klist (Kerberos tickets), nltest /sc_query:domain (secure channel). DNS: dcdiag /test:dns, nslookup -type=srv _ldap._tcp.domain.local. Replication: repadmin /showrepl, repadmin /replsummary. Account lockout: Event ID 4740 on PDC, LockoutStatus.exe (Microsoft tool). Password issues: Check PDC Emulator first. Common issues: time sync (w32tm /query /status), DNS misconfiguration, network connectivity. AD database: ntdsutil for maintenance."
    },
    {
        "question": "What is AD LDS (Lightweight Directory Services)?",
        "answer": "AD LDS (formerly ADAM) is a standalone LDAP directory without AD DS dependencies. Use cases: LDAP-enabled applications, DMZ authentication, directory-aware apps, dev/test. Install: Add-WindowsFeature ADLDS. Create instance: setup wizard or dsdbutil. Each instance: independent, separate port (389 default taken by AD DS), separate NTDS.dit. Schema: customizable, extends default. Access: LDAP clients, ADSI, DirectoryServices. Replication: between AD LDS instances. Not for: Windows authentication, Group Policy. Good for: application-specific directories, proxy authentication."
    },
]

# =============================================================================
# AZURE AD / ENTRA ID
# =============================================================================

AZURE_AD_ENTRA = [
    {
        "question": "What is Azure AD (Entra ID) and how does it differ from on-premises AD?",
        "answer": "Azure AD (now Microsoft Entra ID) is a cloud-based identity service. Key differences: 1) No LDAP - uses REST APIs (Microsoft Graph), 2) No Group Policy - uses Intune/MDM, 3) No Kerberos by default - uses OAuth 2.0/OIDC/SAML, 4) Flat structure - no OUs/forests, 5) Built for internet apps, not network resources. Features: SSO to SaaS apps, MFA, Conditional Access, Identity Protection. Tiers: Free (basic SSO), P1 (conditional access, self-service), P2 (identity protection, PIM). Connect to on-prem: Azure AD Connect for hybrid identity."
    },
    {
        "question": "How do I set up Azure AD Connect for hybrid identity?",
        "answer": "Azure AD Connect syncs on-prem AD to Azure AD. Install on member server (not DC). Sync options: 1) Password Hash Sync (PHS) - hash of hash to cloud, simplest, 2) Pass-through Auth (PTA) - validates against on-prem, 3) Federation (ADFS) - on-prem auth, complex. Setup: Download AADConnect, run wizard, choose sync method, select OUs, configure filtering. Sync schedule: 30 minutes default. Force sync: Start-ADSyncSyncCycle -PolicyType Delta. Staging mode: sync without writing. Troubleshoot: AADConnect wizard, Event Logs, Microsoft Graph API. V2 adds support for groups >50k."
    },
    {
        "question": "What is Conditional Access in Azure AD?",
        "answer": "Conditional Access policies control access based on conditions. Components: Assignments (users, apps, conditions) → Access Controls (grant/block, require MFA). Conditions: user risk, sign-in risk, device platform, location, client app. Grant controls: Require MFA, require compliant device, require hybrid joined, require approved app. Session controls: app enforced restrictions, sign-in frequency, persistent browser. Examples: Require MFA outside corporate network, block legacy auth, require compliant device for Exchange. Create via Portal or PowerShell (Graph API). Report-only mode for testing. Requires Azure AD P1+."
    },
    {
        "question": "How do I configure Azure AD Multi-Factor Authentication (MFA)?",
        "answer": "MFA options: Microsoft Authenticator (push/TOTP), SMS, voice call, hardware tokens (OATH). Configure: 1) Per-user MFA portal (legacy), 2) Conditional Access (recommended), 3) Security Defaults (basic, free tier). Authenticator app: push notifications, passwordless, number matching. Registration: users.microsoft.com or aka.ms/mfasetup. Combined registration: Portal > Azure AD > User settings > Manage user feature settings. For admins: require phishing-resistant MFA. Backup: require 2 methods. Service accounts: use managed identities or exclude with compensating controls. Monitor: Sign-in logs, MFA registration report."
    },
    {
        "question": "What is Privileged Identity Management (PIM)?",
        "answer": "PIM provides just-in-time privileged access. Features: time-bound role activation, approval workflow, MFA on activation, audit trail. Setup: Activate PIM in Azure AD, configure role settings. Activation: User requests role, approver approves (if configured), role granted for duration. Eligible vs Active assignments: Eligible requires activation, Active is permanent. Access reviews: periodic recertification of role assignments. Alert on: privileged role activation, permanent assignments. Best practice: no permanent Global Admin except break-glass. Requires Azure AD P2. Graph API for automation."
    },
    {
        "question": "How do I configure Azure AD Application Registration and Enterprise Apps?",
        "answer": "App registrations: define app identity in your tenant. Enterprise apps: instantiate apps (registered or gallery) for user access. Registration: Portal > App registrations > New. Configure: Redirect URIs, certificates/secrets, API permissions. Permissions: Delegated (act as user), Application (act as app). Consent: user consent, admin consent. Gallery apps: pre-integrated SaaS apps with SSO configured. Provisioning: SCIM-based user/group sync to SaaS apps. Service principals: identity for app/service in directory. Managed identities: automatic identity for Azure resources (preferred over secrets)."
    },
    {
        "question": "What is Azure AD Domain Services?",
        "answer": "Azure AD DS provides managed AD DS in Azure (LDAP, Kerberos, NTLM). Use for: lift-and-shift legacy apps needing AD auth, LDAP queries in cloud. Creates: two DCs in managed VNet, syncs from Azure AD. Features: domain join Azure VMs, Group Policy (limited), LDAP, Kerberos. Limitations: no schema extensions, no trust to on-prem, no DC-level access. Not a DC replacement - can't extend on-prem AD. Setup: Enable in Portal, configure VNet, wait for provisioning (~30 min). DNS: point VNet to managed DS IPs. Password hash sync required for user passwords."
    },
    {
        "question": "How do I troubleshoot Azure AD sign-in issues?",
        "answer": "Sign-in logs: Portal > Azure AD > Sign-in logs. Key fields: Status, Failure reason, Conditional Access, Authentication details. Common issues: 1) MFA not completed - check Authentication details tab, 2) Conditional Access blocked - check CA tab, 3) Account disabled/deleted, 4) Wrong password - check on-prem if hybrid, 5) Guest user issues - check B2B config. Tools: What If tool (test CA policies), Sign-in diagnostic, Microsoft Graph API. Error codes: AADSTS error codes with descriptions. Hybrid: Check Azure AD Connect sync status, password hash sync status. Network: Verify connectivity to login.microsoftonline.com."
    },
    {
        "question": "What is Microsoft Entra Verified ID?",
        "answer": "Verified ID is decentralized identity using verifiable credentials. Concept: organization issues credential to user's wallet, user presents to relying party, cryptographically verified. Use cases: employee onboarding verification, education credentials, age verification. Components: Issuer (creates credentials), Holder (user with Microsoft Authenticator), Verifier (validates credentials). Setup: Azure AD tenant, Key Vault, Verified ID service. Based on: W3C Verifiable Credentials, decentralized identifiers (DIDs). Benefits: user controls data, reduces PII sharing, tamper-proof. Integration via APIs. Alternative to traditional identity proofing services."
    },
]

# =============================================================================
# WINDOWS TROUBLESHOOTING AND TOOLS
# =============================================================================

TROUBLESHOOTING = [
    {
        "question": "How do I use Event Viewer effectively for troubleshooting?",
        "answer": "Event Viewer (eventvwr.msc) logs system events. Key logs: Application (app errors), System (OS/drivers), Security (audit events). Levels: Critical, Error, Warning, Information, Verbose. Filter: Create Custom Views by log, level, event ID, source. Key Event IDs: 41 (unexpected shutdown), 1001 (BSOD), 4624/4625 (logon success/failure), 7001/7023 (service start/fail), 1074 (shutdown initiated). PowerShell: Get-WinEvent -LogName System -MaxEvents 50. Export: wevtutil epl System C:\\system.evtx. Forward events: Windows Event Forwarding for central collection. Performance: limit log sizes, archive old logs."
    },
    {
        "question": "What are the essential Windows troubleshooting tools?",
        "answer": "Built-in: Event Viewer (events), Resource Monitor (real-time perf), Performance Monitor (detailed counters), Reliability Monitor (stability history), Task Manager (processes), msconfig (startup/boot), Device Manager (hardware), msinfo32 (system info). Sysinternals: Process Explorer (advanced task manager), Process Monitor (file/registry/network activity), Autoruns (startup items), PsTools (remote admin). Network: netstat, tracert, pathping, Test-NetConnection. Disk: chkdsk, DISM, sfc /scannow. Memory: Windows Memory Diagnostic (mdsched). Remote: Remote Desktop, WinRM, PSRemoting."
    },
    {
        "question": "How do I troubleshoot Windows performance issues?",
        "answer": "Identify bottleneck: CPU, Memory, Disk, Network. Tools: Task Manager (quick look), Resource Monitor (detailed), Performance Monitor (historical). CPU: high process → Process Explorer for details, check for runaway services. Memory: high committed → find memory hog, check for memory leak. Disk: high queue length → check which process, SSD health, fragmentation (HDD). Steps: 1) Task Manager > Performance tab for overview, 2) Resource Monitor for real-time details, 3) Performance Monitor for data collection. Create Data Collector Set for long-term analysis. PAL tool for automated log analysis."
    },
    {
        "question": "How do I use Windows Recovery Environment (WinRE)?",
        "answer": "WinRE: recovery environment for repair when Windows won't boot. Access: Settings > Recovery > Advanced startup, or boot from install media. Options: Startup Repair (fix boot issues), System Restore (restore point), System Image Recovery (full image restore), Command Prompt (manual repair). Commands: bootrec /fixmbr, bootrec /fixboot, bootrec /rebuildbcd, sfc /scannow /offbootdir=C:\\ /offwindir=C:\\Windows, DISM /Image:C:\\ /Cleanup-Image /RestoreHealth. Safe Mode: Enable networking for updates/drivers. Reset this PC: keep or remove files. Can access WinRE from: boot loop auto (3 failed boots), Shift+Restart."
    },
    {
        "question": "How do I troubleshoot Windows Update issues?",
        "answer": "Common issues: stuck updates, failed installation, high disk usage. Built-in: Settings > Troubleshoot > Windows Update. Manual steps: 1) Stop wuauserv service, 2) Delete C:\\Windows\\SoftwareDistribution, 3) Start wuauserv, 4) Run updates. DISM repair: DISM /Online /Cleanup-Image /RestoreHealth. Reset Windows Update: script that stops services, renames folders, re-registers DLLs. Check CBS.log in C:\\Windows\\Logs\\CBS. Check WindowsUpdate.log: Get-WindowsUpdateLog. Error codes: search 0x80070005 etc. WSUS issues: wuauclt /detectnow /reportnow, Check WUAgent version. Last resort: in-place upgrade repair install."
    },
    {
        "question": "How do I use Process Monitor for troubleshooting?",
        "answer": "Process Monitor (ProcMon) captures real-time file, registry, network, process activity. Download from Sysinternals. Use for: finding 'access denied' causes, tracking what files/registry an app touches, troubleshooting app installation, malware analysis. Filter early: Process Name, Operation, Path, Result. Common patterns: Filter for 'NAME NOT FOUND' to find missing files/registry, filter for 'ACCESS DENIED' for permission issues. Include: Enable 'Show Resolved Network Addresses'. Save: .PML format for sharing. Boot logging: Options > Enable Boot Logging for startup issues. High volume: use filters to reduce noise."
    },
    {
        "question": "How do I troubleshoot Windows authentication and Kerberos?",
        "answer": "Kerberos flow: Client → DC (AS-REQ/AS-REP for TGT) → DC (TGS-REQ/TGS-REP for service ticket) → Server. Tools: klist (view tickets), setspn (manage SPNs), nltest (DC queries). View tickets: klist. Purge tickets: klist purge. Common issues: 1) SPN not found - setspn -L account, 2) Time skew >5 min - w32tm /query /status, 3) Delegation - check account trusted for delegation. Debug: Event log (Security), Network trace, Kerberos logging (enable via registry). Double-hop problem: configure constrained delegation. NTLM fallback: may work when Kerberos fails - check for SPN issues."
    },
    {
        "question": "How do I use Windows Performance Monitor for baselining?",
        "answer": "Performance Monitor (perfmon) collects system metrics. Key counters: Processor\\% Processor Time, Memory\\Available MBytes, PhysicalDisk\\Avg. Disk Queue Length, Network Interface\\Bytes Total/sec. Create Data Collector Set: perfmon > Data Collector Sets > User Defined > New. Schedule: run during typical workload. Analyze: perfmon > Reports > User Defined. Baselines: collect during normal operation, compare during issues. Thresholds: CPU >80% sustained, Available Memory <10% RAM, Disk Queue >2 per disk. Alerts: Create alerts for threshold breaches. Export: logman export for command-line management."
    },
    {
        "question": "What are critical Registry locations for troubleshooting?",
        "answer": "HKLM\\SYSTEM\\CurrentControlSet\\Services: All services configuration. HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run: Machine startup programs. HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run: User startup programs. HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion: Windows version info. HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager: Boot settings, PendingFileRenameOperations. HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server: RDP settings. HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall: Installed programs. HKLM\\SOFTWARE\\Policies + HKCU\\SOFTWARE\\Policies: Group Policy settings. HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa: Security settings. Backup before editing: reg export HKLM\\key backup.reg."
    },
    {
        "question": "How do I diagnose network connectivity issues step by step?",
        "answer": "Systematic approach: 1) Physical: check cable, link lights. 2) IP config: ipconfig - have valid IP? APIPA (169.254.x.x) = DHCP fail. 3) Gateway: ping default gateway - local network issue if fails. 4) DNS: nslookup <target> - resolve fails = DNS issue. 5) Remote host: ping target IP - routing/firewall issue if fails. 6) Application: Test-NetConnection -Port 443 - app/firewall blocking. PowerShell: Get-NetIPConfiguration, Test-NetConnection, Resolve-DnsName. Trace: tracert for path, pathping for quality. Common fixes: ipconfig /release /renew, ipconfig /flushdns, netsh winsock reset. Check for: proxy settings, firewall rules, VPN conflicts."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "How does Windows handle process and memory management?",
        "answer": "Windows uses virtual memory with demand paging. Each process gets its own virtual address space (4GB on 32-bit, 128TB on 64-bit). The Memory Manager handles: working sets (pages in RAM), page file (swap), copy-on-write for efficiency. Process priorities affect CPU scheduling. Memory types: Private (process-specific), Shared (DLLs), Mapped files. Tools: Task Manager, Resource Monitor, RAMMap for detailed analysis."
    },
    {
        "question": "What is Group Policy and how does it work?",
        "answer": "Group Policy is a Windows feature for centralized management of user and computer settings. Policies are stored in Group Policy Objects (GPOs). Processing order: Local, Site, Domain, OU (LSDOU). Computer policies apply at boot, User policies at login. Settings are stored in registry under HKLM\\SOFTWARE\\Policies and HKCU\\SOFTWARE\\Policies. Tools: gpedit.msc (local), gpmc.msc (domain). gpresult shows applied policies."
    },
    {
        "question": "How does Windows networking stack work?",
        "answer": "Windows networking follows a layered model: Winsock API at top, TDI (Transport Driver Interface), Protocol drivers (TCP/IP), NDIS (Network Driver Interface Specification), NIC drivers. Windows Filtering Platform (WFP) enables firewall functionality. DNS Client service caches resolutions. Network profiles (Domain, Private, Public) control firewall rules. SMB handles file sharing over TCP 445."
    },
    {
        "question": "What is the Windows Boot Process?",
        "answer": "UEFI/BIOS initializes hardware, loads Windows Boot Manager (bootmgr) from EFI partition. Boot Manager reads BCD (Boot Configuration Data), loads winload.efi. Winload loads kernel (ntoskrnl.exe), HAL, and boot drivers. Kernel initializes executive subsystems, starts Session Manager (smss.exe). Smss starts csrss.exe and wininit.exe (for Session 0) or winlogon.exe (for user sessions). Services and desktop load after login."
    },
    {
        "question": "How do Windows security permissions work?",
        "answer": "Windows uses Discretionary Access Control Lists (DACLs). Each object has a security descriptor with owner, group, and ACL. ACL contains Access Control Entries (ACEs) specifying trustees and permissions. Permissions are additive except for Deny (checked first). Effective permissions combine explicit + inherited. Special permissions: Full Control, Modify, Read & Execute. SYSTEM account has full access. Administrators can take ownership."
    },
    {
        "question": "What is WMI and when should it be used?",
        "answer": "Windows Management Instrumentation (WMI) is an infrastructure for managing Windows systems. It provides a consistent interface to hardware, OS, and application information. WMI uses a hierarchical namespace (root\\cimv2 is common). Query using WQL (similar to SQL). PowerShell cmdlets: Get-WmiObject (legacy), Get-CimInstance (modern, uses WinRM). Use cases: inventory, monitoring, remote administration. CIM cmdlets preferred for better performance and remoting."
    },
    # === WINDOWS SERVER 2019+/2022, AZURE LOCAL, EXCHANGE ===
    {
        "question": "What is Windows Admin Center and how does it replace traditional tools?",
        "answer": "Windows Admin Center (WAC) is a modern, browser-based management tool for Windows Server 2016+ and Windows 10+. It consolidates: Server Manager, MMC snap-ins, Remote Desktop, PowerShell. Features: cluster management, Azure hybrid integration, certificate management, Hyper-V management. Deployment: gateway mode (central server) or desktop mode. Extensions add functionality. Connects via WinRM/PowerShell remoting. Replaces need for RDP for most admin tasks. Free, included with Windows Server."
    },
    {
        "question": "How does Storage Spaces Direct (S2D) work in Windows Server?",
        "answer": "Storage Spaces Direct (S2D) creates software-defined storage from local drives across cluster nodes. Available in Windows Server 2016+ Datacenter and Azure Stack HCI. Architecture: Pool (all drives combined), Virtual Disks (volumes with resiliency), ReFS file system. Resiliency: Mirror (2-3 copies), Parity (like RAID5/6), Mirror-Accelerated Parity. Cache tier uses NVMe/SSD, capacity uses HDD. Requires: 2-16 nodes, 10GbE+ RDMA networking, same hardware across nodes. Managed via WAC or PowerShell."
    },
    {
        "question": "What is Azure Stack HCI (Azure Local)?",
        "answer": "Azure Stack HCI (recently renamed Azure Local) is a hyperconverged infrastructure OS for running VMs on-premises with Azure integration. Built on Windows Server with S2D storage. Key features: Azure Arc integration (manage from Azure portal), Azure Kubernetes Service, Azure Virtual Desktop support, Azure Benefits (licensing). Requires: Azure subscription, validated hardware, 2-16 node cluster. Deployment: WAC or PowerShell. Billing: per-core subscription. Unlike Azure Stack Hub, workloads run entirely on-premises. Updates via Azure Update Management."
    },
    {
        "question": "How do I configure Windows Server Failover Clustering?",
        "answer": "Failover Clustering provides high availability. Setup: Install Failover Clustering feature, run Cluster Validation wizard, create cluster. Components: Cluster nodes, quorum (voting for split-brain), Cluster Shared Volumes (CSV), Cluster Network. Quorum modes: Node Majority, Disk Witness, File Share Witness, Cloud Witness (Azure blob). PowerShell: New-Cluster, Add-ClusterNode, Get-ClusterResource. Requirements: identical hardware, shared storage or S2D, domain membership. CSV enables multiple nodes to access same volume."
    },
    {
        "question": "What's new in Windows Server 2022 for networking?",
        "answer": "Windows Server 2022 networking improvements: SMB over QUIC (secure file access without VPN), SMB compression (on-the-fly), TLS 1.3 default, DNS-over-HTTPS (DoH), Secure DNS, TCP improvements (HyStart++, RACK, BBRv2). SMB over QUIC enables remote file access through firewalls using UDP 443. HTTPS boot support for Secured-core servers. Time-based key for AD authentication. Enhanced SDN with improved container networking. Better support for SR-IOV and RDMA."
    },
    {
        "question": "How does Exchange Server hybrid configuration work?",
        "answer": "Exchange Hybrid connects on-premises Exchange to Microsoft 365/Exchange Online. Hybrid Configuration Wizard (HCW) sets up: OAuth, federation trust, mail flow connectors, free/busy sharing. Mailbox migrations: native batch migration to Exchange Online. Features: cross-premises mail routing, shared GAL, calendar availability. Requirements: Exchange 2016+ for full features, Azure AD Connect for identity sync. Mail flow options: centralized (through on-prem) or decentralized. Consider: certificate requirements, namespace planning, firewall rules (25/443)."
    },
    {
        "question": "What is Exchange Online Protection and Defender for Office 365?",
        "answer": "Exchange Online Protection (EOP) is baseline email security: anti-spam, anti-malware, connection filtering, mail flow rules. Included with Exchange Online. Defender for Office 365 Plan 1 adds: Safe Attachments (detonation), Safe Links (URL rewriting), anti-phishing policies. Plan 2 adds: Threat Explorer, automated investigation, Attack Simulation Training, Threat Trackers. For on-premises Exchange: standalone EOP available. Configure via Security & Compliance Center or PowerShell. Uses ML and sandbox detonation."
    },
    {
        "question": "How do I manage Exchange Server with PowerShell?",
        "answer": "Exchange Management Shell (EMS) is the primary admin interface. Connect: Add-PSSnapin Microsoft.Exchange.Management.PowerShell.SnapIn (on-prem) or Connect-ExchangeOnline (cloud). Key cmdlets: Get-Mailbox, Set-Mailbox, Get-TransportRule, New-MailboxExportRequest, Get-MessageTrackingLog. Bulk operations: Get-Mailbox -ResultSize Unlimited | Set-Mailbox -ProhibitSendQuota 5GB. Remote PowerShell for EXO uses modern auth. Exchange Online v2 module (EXO V2) recommended for performance with REST API support."
    },
    {
        "question": "What is Software Defined Networking (SDN) in Windows Server?",
        "answer": "Windows Server SDN provides programmable network virtualization. Components: Network Controller (REST API management), Software Load Balancer, Datacenter Firewall, RAS Gateway. Features: VXLAN encapsulation, micro-segmentation, distributed firewall, NAT. Network Controller manages: virtual networks, access control lists, QoS policies, gateway pools. Deployment: WAC, SCVMM, or PowerShell. Use cases: multi-tenant isolation, network policies as code, container networking. Integrates with Azure Stack HCI. NVGRE or VXLAN for overlay networks."
    },
    {
        "question": "How does Active Directory Federation Services (ADFS) work?",
        "answer": "ADFS provides claims-based identity federation and SSO. Architecture: Federation Server (issues tokens), Web Application Proxy (reverse proxy), Relying Parties (apps trusting ADFS). Authentication flow: user requests resource → redirected to ADFS → authenticates → receives SAML/JWT token → accesses resource. Supports: SAML 2.0, WS-Federation, OAuth 2.0, OpenID Connect. Modern replacement: Azure AD with Application Proxy. Still needed for: on-premises apps, specific federation scenarios. Consider Azure AD for new deployments."
    },
    {
        "question": "What is Shielded VMs and Host Guardian Service?",
        "answer": "Shielded VMs protect VMs from compromised fabric administrators. Host Guardian Service (HGS) attests hosts before allowing access to VM encryption keys. Attestation modes: TPM (hardware), Host Key (software), Admin-trusted (deprecated). VM shielding encrypts VM state, protects from live inspection, restricts management actions. Requirements: Windows Server Datacenter, TPM 2.0 for TPM attestation, Hyper-V hosts in guarded fabric. Key Protector (KP) file contains encryption keys. Use for high-security workloads."
    },
    {
        "question": "How do I implement Windows Server backup and recovery strategies?",
        "answer": "Windows Server Backup (wbadmin): built-in, supports bare-metal recovery, system state, file-level. Azure Backup: MARS agent for files/folders, DPM/MABS for applications. System State includes: AD, Registry, COM+, Certificate Services. Best practices: 3-2-1 rule (3 copies, 2 media types, 1 offsite), test restores regularly. For Hyper-V: checkpoint vs backup (checkpoint not backup!). Cluster-aware backup for failover clusters. Azure Site Recovery for disaster recovery to cloud. DFSR for file replication."
    },
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "I want to delete System32 to free up space",
        "error_type": "dangerous_operation",
        "response": {
            "status": "blocked",
            "severity": "critical",
            "message": "STOP - This would make Windows unbootable",
            "explanation": "System32 contains essential Windows operating system files. Deleting it would prevent Windows from starting and require a complete reinstall. If you need to free space, use Disk Cleanup (cleanmgr), uninstall unused programs, or clear temporary files from %TEMP%.",
            "safe_alternatives": [
                "Run Disk Cleanup: cleanmgr /d C:",
                "Clear temp files: Remove-Item $env:TEMP\\* -Recurse -Force",
                "Uninstall programs: Get-Package | Where DisplayName -like '*unused*' | Uninstall-Package",
                "Find large files: Get-ChildItem -Path C:\\ -Recurse -File | Sort Length -Descending | Select -First 20"
            ]
        }
    },
    {
        "instruction": "Run this downloaded PowerShell script from the internet",
        "error_type": "security_warning",
        "response": {
            "status": "needs_review",
            "severity": "high",
            "warnings": [
                "Never run scripts from untrusted sources without reviewing them",
                "Scripts can execute any command with your permissions",
                "Malicious scripts may steal credentials, install malware, or damage files"
            ],
            "safe_approach": [
                "Read the entire script first: Get-Content script.ps1",
                "Check for obfuscation (encoded commands, invoke-expression)",
                "Look for suspicious: Invoke-WebRequest to unknown URLs, encoded commands, registry modifications",
                "Run in a VM or sandbox if unsure",
                "Use VirusTotal to scan the file"
            ]
        }
    },
    {
        "instruction": "The command returned Access Denied",
        "error_type": "permissions",
        "response": {
            "status": "recoverable",
            "common_causes": [
                "Command requires administrator privileges",
                "File/folder owned by SYSTEM or another user",
                "Antivirus blocking the operation",
                "File is locked by another process"
            ],
            "solutions": [
                "Run PowerShell as Administrator (right-click, Run as Administrator)",
                "Check who owns the file: Get-Acl <path>",
                "Take ownership: takeown /f <path> /r /d y",
                "Grant permissions: icacls <path> /grant $env:USERNAME:F",
                "Check if file is locked: handle.exe <path> (Sysinternals)"
            ],
            "caution": "Don't blindly take ownership of system files - understand why access is denied first"
        }
    },
    {
        "instruction": "PowerShell execution policy is preventing my script from running",
        "error_type": "policy_restriction",
        "response": {
            "status": "recoverable",
            "explanation": "Execution policy is a safety feature, not a security boundary",
            "policies": {
                "Restricted": "No scripts allowed",
                "AllSigned": "Only signed scripts",
                "RemoteSigned": "Local scripts okay, downloaded must be signed",
                "Unrestricted": "All scripts run (warns for downloaded)",
                "Bypass": "Nothing blocked, no warnings"
            },
            "solutions": [
                "For current session: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass",
                "For current user: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned",
                "Run single script: powershell -ExecutionPolicy Bypass -File script.ps1",
                "Unblock downloaded file: Unblock-File script.ps1"
            ],
            "recommendation": "Use RemoteSigned for development machines - balances security and convenience"
        }
    },
    {
        "instruction": "Windows says the file is in use and can't be deleted",
        "error_type": "file_lock",
        "response": {
            "status": "recoverable",
            "diagnostic_steps": [
                "Find what's using the file: handle.exe <filename> (Sysinternals)",
                "Or use Resource Monitor > CPU > Associated Handles"
            ],
            "solutions": [
                "Close the application using the file",
                "Kill the process: Stop-Process -Name <processname> -Force",
                "Delete on reboot: MoveFileEx with MOVEFILE_DELAY_UNTIL_REBOOT",
                "Use Unlocker tool as last resort"
            ],
            "common_culprits": [
                "Explorer.exe for folders",
                "SearchIndexer for indexed files",
                "Antivirus scanning",
                "Backup software"
            ]
        }
    },
    {
        "instruction": "Blue screen of death (BSOD) - how do I fix it?",
        "error_type": "system_crash",
        "response": {
            "status": "needs_investigation",
            "immediate_steps": [
                "Note the stop code (e.g., CRITICAL_PROCESS_DIED, IRQL_NOT_LESS_OR_EQUAL)",
                "Boot into Safe Mode if system won't start normally",
                "Check Event Viewer > Windows Logs > System for critical errors"
            ],
            "common_causes": {
                "DRIVER_IRQL_NOT_LESS_OR_EQUAL": "Driver issue - update or rollback drivers",
                "CRITICAL_PROCESS_DIED": "System file corruption - run sfc /scannow",
                "PAGE_FAULT_IN_NONPAGED_AREA": "RAM issue - run memory diagnostic",
                "KERNEL_SECURITY_CHECK_FAILURE": "Driver or hardware incompatibility"
            },
            "diagnostic_tools": [
                "Windows Memory Diagnostic: mdsched.exe",
                "System File Checker: sfc /scannow",
                "DISM: DISM /Online /Cleanup-Image /RestoreHealth",
                "BlueScreenView (NirSoft) for dump analysis"
            ]
        }
    },
    {
        "instruction": "How do I disable Windows Defender completely?",
        "error_type": "security_warning",
        "response": {
            "status": "discouraged",
            "warning": "Disabling Windows Defender leaves your system vulnerable to malware",
            "legitimate_reasons": [
                "Running another antivirus (Defender disables automatically)",
                "Performance testing",
                "False positive blocking required software"
            ],
            "if_really_needed": [
                "Temporary: Windows Security > Virus & threat protection > Real-time protection OFF",
                "Permanent: Requires Group Policy or registry changes",
                "Better: Add exclusions for specific files/folders instead"
            ],
            "recommendation": "Add exclusions rather than disabling. Set-MpPreference -ExclusionPath 'C:\\DevFolder'"
        }
    },
    {
        "instruction": "I accidentally deleted important files, can they be recovered?",
        "error_type": "data_recovery",
        "response": {
            "status": "potentially_recoverable",
            "immediate_actions": [
                "STOP using the drive immediately - new data may overwrite deleted files",
                "Don't install recovery software on the same drive"
            ],
            "recovery_options": [
                "Check Recycle Bin first",
                "Previous Versions: Right-click folder > Properties > Previous Versions",
                "Shadow Copies: vssadmin list shadows",
                "File History backup if enabled",
                "Third-party tools: Recuva, TestDisk, PhotoRec"
            ],
            "prevention": "Enable File History, set up regular backups, consider OneDrive for important files"
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    """Format as command execution response."""
    return json.dumps({
        "action": "execute_command",
        "shell": "powershell",
        "command": command,
        "explanation": explanation,
        "requires_admin": "HKLM" in command or "Stop-Service" in command or "Set-Service" in command
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    """Format as multi-step plan."""
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
        "requires_confirmation": True
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    """Format error/guardrail response."""
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    """Generate tool selection training examples."""
    examples = []
    
    all_tasks = BASIC_POWERSHELL_TASKS + ADVANCED_POWERSHELL_TASKS + SERVICE_MANAGEMENT_TASKS + REGISTRY_TASKS
    
    for task in all_tasks:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_command_response(task["command"], task["explanation"])
        })
    
    return examples

def generate_planning_examples() -> List[Dict]:
    """Generate multi-step planning examples."""
    examples = []
    
    for task in PLANNING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_planning_response(task["steps"])
        })
    
    return examples

def generate_concept_examples() -> List[Dict]:
    """Generate concept Q&A examples."""
    examples = []
    
    # Include all concept/knowledge-based sections
    all_concepts = (
        BASIC_CONCEPTS + 
        ADVANCED_CONCEPTS + 
        DNS_DHCP_NETWORKING + 
        ACTIVE_DIRECTORY + 
        AZURE_AD_ENTRA + 
        TROUBLESHOOTING
    )
    
    for concept in all_concepts:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": concept["question"],
            "response": concept["answer"]
        })
    
    return examples

def generate_error_examples() -> List[Dict]:
    """Generate error handling examples."""
    examples = []
    
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    
    return examples

def generate_variations() -> List[Dict]:
    """Generate additional variations."""
    variations = []
    
    # Common admin tasks with variations
    admin_variations = [
        ("How do I see what's using all my RAM?", "Use Task Manager (Ctrl+Shift+Esc) > Memory column, or PowerShell: Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 Name, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet/1MB,2)}}"),
        ("My computer is running slow, what should I check?", "Check: 1) Task Manager for CPU/Memory hogs, 2) Startup programs (Task Manager > Startup), 3) Disk usage (Resource Monitor), 4) Windows Update pending, 5) Antivirus scanning, 6) Disk health. PowerShell: Get-Process | Sort CPU -Descending | Select -First 5"),
        ("How do I find my IP address?", "PowerShell: (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*'}).IPAddress. Or simply: ipconfig. For public IP: (Invoke-WebRequest -Uri 'https://api.ipify.org').Content"),
        ("How do I open ports in Windows Firewall?", "PowerShell: New-NetFirewallRule -DisplayName 'My App' -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow. Or use Windows Defender Firewall with Advanced Security (wf.msc)."),
        ("How to check Windows license status?", "Run: slmgr /xpr for expiration, slmgr /dli for license info, slmgr /dlv for detailed info. PowerShell: Get-CimInstance SoftwareLicensingProduct | Where PartialProductKey | Select Name, LicenseStatus"),
    ]
    
    for query, answer in admin_variations:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    # PowerShell tips
    ps_tips = [
        ("What's the PowerShell equivalent of grep?", "Select-String is PowerShell's grep: Get-Content file.txt | Select-String 'pattern'. For recursive search: Get-ChildItem -Recurse *.log | Select-String 'error'. Alias: sls. Supports regex by default."),
        ("How do I pipe commands in PowerShell?", "PowerShell pipes objects, not text: Get-Process | Where-Object {$_.CPU -gt 100} | Sort-Object CPU -Descending. The pipeline passes full objects, so you can access properties directly. Use ForEach-Object (%) for per-item processing."),
        ("What's the difference between = and -eq in PowerShell?", "= is assignment: $x = 5. -eq is comparison: if ($x -eq 5). PowerShell comparison operators: -eq (equal), -ne (not equal), -gt, -lt, -ge, -le, -like (wildcard), -match (regex). They're case-insensitive by default; use -ceq for case-sensitive."),
    ]
    
    for query, answer in ps_tips:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    return variations

def main():
    """Generate all Windows training data."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Windows System Administration Training Data")
    print("=" * 60)
    
    all_examples = []
    
    # Generate each category
    print("\n1. Generating tool selection examples...")
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"   Generated {len(tool_examples)} examples")
    
    print("\n2. Generating planning examples...")
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"   Generated {len(planning_examples)} examples")
    
    print("\n3. Generating concept Q&A...")
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"   Generated {len(concept_examples)} examples")
    
    print("\n4. Generating error/guardrail scenarios...")
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"   Generated {len(error_examples)} examples")
    
    print("\n5. Generating variations...")
    variations = generate_variations()
    all_examples.extend(variations)
    print(f"   Generated {len(variations)} examples")
    
    # Shuffle for training
    random.shuffle(all_examples)
    
    # Save to JSONL
    output_file = output_dir / "windows_admin.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Windows Training Data Generation Complete!")
    print("=" * 60)
    print(f"Total examples: {len(all_examples)}")
    print(f"  Tool selection: {len(tool_examples)}")
    print(f"  Planning: {len(planning_examples)}")
    print(f"  Concepts: {len(concept_examples)}")
    print(f"  Error handling: {len(error_examples)}")
    print(f"  Variations: {len(variations)}")

if __name__ == "__main__":
    main()
