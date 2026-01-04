#!/usr/bin/env python3
"""
Linux System Administration Training Data Generator
Target: ~400 examples for bash, systemd, networking, permissions, troubleshooting
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for Linux system administration.
You help with bash scripting, system configuration, systemd services, networking, and Linux management tasks."""

# =============================================================================
# TOOL SELECTION TASKS - Basic Commands
# =============================================================================

BASIC_BASH_TASKS = [
    {
        "instruction": "List all files including hidden ones",
        "command": "ls -la",
        "explanation": "Lists all files with details; -a shows hidden files, -l shows long format"
    },
    {
        "instruction": "Find files modified in the last 24 hours",
        "command": "find . -type f -mtime -1",
        "explanation": "Finds files modified within last day; -mtime -1 means less than 1 day"
    },
    {
        "instruction": "Show disk usage summary",
        "command": "df -h",
        "explanation": "Shows filesystem disk usage in human-readable format"
    },
    {
        "instruction": "Check memory usage",
        "command": "free -h",
        "explanation": "Displays memory usage in human-readable format"
    },
    {
        "instruction": "Show running processes",
        "command": "ps aux",
        "explanation": "Lists all processes with detailed information"
    },
    {
        "instruction": "Find a process by name",
        "command": "pgrep -a nginx",
        "explanation": "Finds processes matching 'nginx' and shows command line"
    },
    {
        "instruction": "Show network connections",
        "command": "ss -tuln",
        "explanation": "Shows TCP/UDP listening sockets; modern replacement for netstat"
    },
    {
        "instruction": "Check system uptime and load",
        "command": "uptime",
        "explanation": "Shows how long system has been running and load averages"
    },
    {
        "instruction": "View system logs",
        "command": "journalctl -xe",
        "explanation": "Shows recent journal entries with explanations for errors"
    },
    {
        "instruction": "Search for text in files",
        "command": "grep -r 'pattern' /path/to/search",
        "explanation": "Recursively searches for pattern in files"
    },
    {
        "instruction": "Show file contents with line numbers",
        "command": "cat -n filename",
        "explanation": "Displays file contents with line numbers"
    },
    {
        "instruction": "Monitor log file in real-time",
        "command": "tail -f /var/log/syslog",
        "explanation": "Follows log file and shows new entries as they appear"
    },
    {
        "instruction": "Check who is logged in",
        "command": "who -a",
        "explanation": "Shows all logged in users with additional info"
    },
    {
        "instruction": "Show environment variables",
        "command": "env | sort",
        "explanation": "Lists all environment variables sorted alphabetically"
    },
    # NEW: Additional basic bash tasks
    {
        "instruction": "Create a new directory",
        "command": "mkdir -p /path/to/new/directory",
        "explanation": "Creates directory and parent directories if needed"
    },
    {
        "instruction": "Copy files recursively",
        "command": "cp -r source/ destination/",
        "explanation": "Copies directory and contents recursively"
    },
    {
        "instruction": "Move or rename a file",
        "command": "mv oldname.txt newname.txt",
        "explanation": "Moves or renames a file or directory"
    },
    {
        "instruction": "Delete a file",
        "command": "rm filename.txt",
        "explanation": "Removes a file; use -f to force, -r for directories"
    },
    {
        "instruction": "Delete a directory recursively",
        "command": "rm -rf /path/to/directory",
        "explanation": "Removes directory and all contents; use with caution"
    },
    {
        "instruction": "Show current working directory",
        "command": "pwd",
        "explanation": "Prints the current working directory path"
    },
    {
        "instruction": "Change directory",
        "command": "cd /var/log",
        "explanation": "Changes to the /var/log directory"
    },
    {
        "instruction": "Go to home directory",
        "command": "cd ~ # or just cd",
        "explanation": "Changes to the user's home directory"
    },
    {
        "instruction": "Show first 20 lines of file",
        "command": "head -n 20 filename",
        "explanation": "Displays the first 20 lines of a file"
    },
    {
        "instruction": "Show last 20 lines of file",
        "command": "tail -n 20 filename",
        "explanation": "Displays the last 20 lines of a file"
    },
    {
        "instruction": "Count lines in a file",
        "command": "wc -l filename",
        "explanation": "Counts and displays the number of lines"
    },
    {
        "instruction": "Sort file contents",
        "command": "sort filename",
        "explanation": "Sorts lines alphabetically; use -n for numeric sort"
    },
    {
        "instruction": "Remove duplicate lines",
        "command": "sort filename | uniq",
        "explanation": "Sorts and removes adjacent duplicate lines"
    },
    {
        "instruction": "Show unique lines with count",
        "command": "sort filename | uniq -c",
        "explanation": "Shows count of each unique line"
    },
    {
        "instruction": "Find a file by name",
        "command": "find / -name 'filename.txt' 2>/dev/null",
        "explanation": "Searches entire filesystem for file, suppresses permission errors"
    },
    {
        "instruction": "Find directories only",
        "command": "find . -type d -name 'logs'",
        "explanation": "Finds directories named 'logs'"
    },
    {
        "instruction": "Show file type",
        "command": "file filename",
        "explanation": "Determines and displays file type"
    },
    {
        "instruction": "Show file permissions in octal",
        "command": "stat -c '%a %n' filename",
        "explanation": "Shows permissions in numeric format"
    },
    {
        "instruction": "Change file owner",
        "command": "sudo chown user:group filename",
        "explanation": "Changes owner and group of a file"
    },
    {
        "instruction": "Change file permissions",
        "command": "chmod 644 filename",
        "explanation": "Sets read/write for owner, read for others"
    },
    {
        "instruction": "Make file executable",
        "command": "chmod +x script.sh",
        "explanation": "Adds execute permission to a file"
    },
    {
        "instruction": "Show command history",
        "command": "history | tail -50",
        "explanation": "Shows last 50 commands from history"
    },
    {
        "instruction": "Search command history",
        "command": "history | grep ssh",
        "explanation": "Finds previous commands containing 'ssh'"
    },
    {
        "instruction": "Clear terminal screen",
        "command": "clear",
        "explanation": "Clears the terminal display"
    },
    {
        "instruction": "Show current date and time",
        "command": "date",
        "explanation": "Displays current date and time"
    },
    {
        "instruction": "Show calendar",
        "command": "cal",
        "explanation": "Displays calendar for current month"
    },
    {
        "instruction": "Check disk space of current directory",
        "command": "du -sh .",
        "explanation": "Shows total size of current directory"
    },
    {
        "instruction": "Find empty files",
        "command": "find . -type f -empty",
        "explanation": "Finds all empty files in current directory tree"
    },
    {
        "instruction": "Find empty directories",
        "command": "find . -type d -empty",
        "explanation": "Finds all empty directories"
    },
    {
        "instruction": "Check system hostname",
        "command": "hostname",
        "explanation": "Shows the system's hostname"
    },
    {
        "instruction": "Show kernel version",
        "command": "uname -r",
        "explanation": "Displays the Linux kernel version"
    },
    {
        "instruction": "Show system information",
        "command": "uname -a",
        "explanation": "Shows all system information including kernel, hostname, architecture"
    },
    {
        "instruction": "Show distribution info",
        "command": "cat /etc/os-release",
        "explanation": "Displays Linux distribution information"
    },
    {
        "instruction": "Check CPU information",
        "command": "lscpu",
        "explanation": "Shows detailed CPU architecture information"
    },
    {
        "instruction": "List USB devices",
        "command": "lsusb",
        "explanation": "Lists connected USB devices"
    },
    {
        "instruction": "List PCI devices",
        "command": "lspci",
        "explanation": "Lists PCI devices (network cards, graphics, etc.)"
    },
    {
        "instruction": "Show block devices",
        "command": "lsblk",
        "explanation": "Lists block devices (disks, partitions)"
    },
    {
        "instruction": "Check last system boot time",
        "command": "who -b",
        "explanation": "Shows when the system was last booted"
    },
    {
        "instruction": "Check last logins",
        "command": "last -10",
        "explanation": "Shows last 10 user logins"
    },
    {
        "instruction": "Redirect output to file",
        "command": "command > output.txt",
        "explanation": "Redirects stdout to file, overwrites existing"
    },
    {
        "instruction": "Append output to file",
        "command": "command >> output.txt",
        "explanation": "Appends stdout to file without overwriting"
    },
    {
        "instruction": "Redirect errors to file",
        "command": "command 2> errors.txt",
        "explanation": "Redirects stderr to file"
    },
    {
        "instruction": "Redirect both output and errors",
        "command": "command &> all_output.txt",
        "explanation": "Redirects both stdout and stderr to file"
    },
    {
        "instruction": "Pipe output to another command",
        "command": "cat file.txt | grep pattern | sort",
        "explanation": "Chains commands using pipes"
    },
    {
        "instruction": "Run command in background",
        "command": "long_running_command &",
        "explanation": "Runs command in background, returns control to terminal"
    },
    {
        "instruction": "Show background jobs",
        "command": "jobs",
        "explanation": "Lists background jobs in current shell"
    },
    {
        "instruction": "Bring job to foreground",
        "command": "fg %1",
        "explanation": "Brings job number 1 to foreground"
    },
]

ADVANCED_BASH_TASKS = [
    {
        "instruction": "Find largest files in directory",
        "command": "find . -type f -exec du -h {} + | sort -rh | head -20",
        "explanation": "Finds files, gets sizes, sorts by size descending, shows top 20"
    },
    {
        "instruction": "Find and delete files older than 30 days",
        "command": "find /var/log -type f -name '*.log' -mtime +30 -delete",
        "explanation": "Finds log files older than 30 days and deletes them"
    },
    {
        "instruction": "Archive directory with compression",
        "command": "tar -czvf archive.tar.gz /path/to/directory",
        "explanation": "Creates gzip-compressed tar archive; -c create, -z gzip, -v verbose, -f file"
    },
    {
        "instruction": "Sync directories with rsync",
        "command": "rsync -avz --progress /source/ /destination/",
        "explanation": "Syncs directories preserving attributes; -a archive, -v verbose, -z compress"
    },
    {
        "instruction": "Monitor system resources in real-time",
        "command": "htop",
        "explanation": "Interactive process viewer; better than top. Install with apt install htop"
    },
    {
        "instruction": "Find process using specific port",
        "command": "lsof -i :8080",
        "explanation": "Lists processes using port 8080"
    },
    {
        "instruction": "Kill all processes by name",
        "command": "pkill -9 processname",
        "explanation": "Sends SIGKILL to all processes matching name"
    },
    {
        "instruction": "Watch command output continuously",
        "command": "watch -n 2 'df -h'",
        "explanation": "Runs df -h every 2 seconds and displays output"
    },
    {
        "instruction": "Create symbolic link",
        "command": "ln -s /path/to/target /path/to/link",
        "explanation": "Creates symbolic link pointing to target"
    },
    {
        "instruction": "Change file permissions recursively",
        "command": "chmod -R 755 /path/to/directory",
        "explanation": "Sets rwxr-xr-x permissions on directory and contents"
    },
    {
        "instruction": "Find files by content and replace",
        "command": "find . -type f -name '*.txt' -exec sed -i 's/old/new/g' {} +",
        "explanation": "Finds txt files and replaces 'old' with 'new' in-place"
    },
    {
        "instruction": "Show directory size breakdown",
        "command": "du -sh */ | sort -rh",
        "explanation": "Shows size of each subdirectory, sorted by size"
    },
    {
        "instruction": "Extract specific columns from file",
        "command": "awk '{print $1, $3}' filename",
        "explanation": "Prints first and third columns from each line"
    },
    {
        "instruction": "Count lines, words, characters",
        "command": "wc -lwc filename",
        "explanation": "Counts lines, words, and characters in file"
    },
    {
        "instruction": "Compare two files",
        "command": "diff -u file1 file2",
        "explanation": "Shows unified diff between files"
    },
    # NEW: Additional advanced bash tasks
    {
        "instruction": "Extract tar.gz archive",
        "command": "tar -xzvf archive.tar.gz -C /destination/",
        "explanation": "Extracts gzip tar archive to specified directory"
    },
    {
        "instruction": "Create tar.bz2 archive",
        "command": "tar -cjvf archive.tar.bz2 /path/to/directory",
        "explanation": "Creates bzip2-compressed tar archive (better compression)"
    },
    {
        "instruction": "Extract tar.xz archive",
        "command": "tar -xJvf archive.tar.xz",
        "explanation": "Extracts xz-compressed tar archive"
    },
    {
        "instruction": "Find files larger than 100MB",
        "command": "find / -type f -size +100M 2>/dev/null | xargs ls -lh",
        "explanation": "Finds files over 100MB and shows details"
    },
    {
        "instruction": "Find files by extension",
        "command": "find . -type f \\( -name '*.log' -o -name '*.txt' \\)",
        "explanation": "Finds files with .log or .txt extensions"
    },
    {
        "instruction": "Delete files but keep directory structure",
        "command": "find . -type f -delete",
        "explanation": "Deletes all files but preserves directories"
    },
    {
        "instruction": "Find and replace text in multiple files",
        "command": "grep -rl 'oldtext' . | xargs sed -i 's/oldtext/newtext/g'",
        "explanation": "Finds files containing text and replaces it"
    },
    {
        "instruction": "Show disk I/O statistics",
        "command": "iostat -xz 1 5",
        "explanation": "Shows extended I/O stats every 1 second, 5 times"
    },
    {
        "instruction": "Monitor disk I/O by process",
        "command": "iotop -o",
        "explanation": "Shows only processes doing I/O; requires root"
    },
    {
        "instruction": "Check file system for errors",
        "command": "sudo fsck -n /dev/sda1",
        "explanation": "Checks filesystem without making changes (-n for no-modify)"
    },
    {
        "instruction": "Mount an ISO file",
        "command": "sudo mount -o loop image.iso /mnt/iso",
        "explanation": "Mounts ISO file as loop device"
    },
    {
        "instruction": "Unmount a filesystem",
        "command": "sudo umount /mnt/usb",
        "explanation": "Unmounts the specified mount point"
    },
    {
        "instruction": "Force unmount a busy filesystem",
        "command": "sudo umount -l /mnt/stuck",
        "explanation": "Lazy unmount - detaches immediately, cleans up when not busy"
    },
    {
        "instruction": "Show mounted filesystems",
        "command": "mount | column -t",
        "explanation": "Lists all mounts in formatted columns"
    },
    {
        "instruction": "Check SMART disk health",
        "command": "sudo smartctl -a /dev/sda",
        "explanation": "Shows SMART health data for disk"
    },
    {
        "instruction": "Run SMART disk test",
        "command": "sudo smartctl -t short /dev/sda",
        "explanation": "Runs short SMART self-test"
    },
    {
        "instruction": "List all users on system",
        "command": "cut -d: -f1 /etc/passwd | sort",
        "explanation": "Extracts usernames from passwd file"
    },
    {
        "instruction": "List users with login shells",
        "command": "grep -v 'nologin\\|false' /etc/passwd | cut -d: -f1",
        "explanation": "Shows only users who can log in"
    },
    {
        "instruction": "Show user's groups",
        "command": "groups username",
        "explanation": "Lists all groups the user belongs to"
    },
    {
        "instruction": "Add user to group",
        "command": "sudo usermod -aG groupname username",
        "explanation": "Adds user to group (-a append, -G supplementary group)"
    },
    {
        "instruction": "Remove user from group",
        "command": "sudo gpasswd -d username groupname",
        "explanation": "Removes user from the specified group"
    },
    {
        "instruction": "Lock a user account",
        "command": "sudo usermod -L username",
        "explanation": "Locks the user account (disables password login)"
    },
    {
        "instruction": "Unlock a user account",
        "command": "sudo usermod -U username",
        "explanation": "Unlocks a previously locked user account"
    },
    {
        "instruction": "Set password expiry",
        "command": "sudo chage -M 90 username",
        "explanation": "Sets maximum password age to 90 days"
    },
    {
        "instruction": "Force password change on next login",
        "command": "sudo chage -d 0 username",
        "explanation": "Forces user to change password at next login"
    },
    {
        "instruction": "Show cron jobs for current user",
        "command": "crontab -l",
        "explanation": "Lists cron jobs for current user"
    },
    {
        "instruction": "Show all system cron jobs",
        "command": "cat /etc/crontab && ls -la /etc/cron.*",
        "explanation": "Shows system crontab and cron directories"
    },
    {
        "instruction": "Edit cron jobs",
        "command": "crontab -e",
        "explanation": "Opens crontab in editor for current user"
    },
    {
        "instruction": "Create a scheduled job with systemd timer",
        "command": "systemctl list-timers --all",
        "explanation": "Lists all systemd timers (modern alternative to cron)"
    },
    {
        "instruction": "Check system load over time",
        "command": "sar -u 1 10",
        "explanation": "Shows CPU usage every 1 second, 10 samples"
    },
    {
        "instruction": "Show top CPU-consuming processes",
        "command": "ps aux --sort=-%cpu | head -20",
        "explanation": "Lists processes sorted by CPU usage descending"
    },
    {
        "instruction": "Show top memory-consuming processes",
        "command": "ps aux --sort=-%mem | head -20",
        "explanation": "Lists processes sorted by memory usage descending"
    },
    {
        "instruction": "Kill process by port",
        "command": "fuser -k 8080/tcp",
        "explanation": "Kills process using TCP port 8080"
    },
    {
        "instruction": "Send signal to process group",
        "command": "kill -TERM -$(pgrep -o processname)",
        "explanation": "Sends TERM signal to process group"
    },
    {
        "instruction": "Run command with timeout",
        "command": "timeout 30s command",
        "explanation": "Runs command, kills it after 30 seconds if still running"
    },
    {
        "instruction": "Run command with nice priority",
        "command": "nice -n 19 command",
        "explanation": "Runs command with lowest priority (19)"
    },
    {
        "instruction": "Change running process priority",
        "command": "renice -n 10 -p 1234",
        "explanation": "Changes priority of process 1234 to 10"
    },
    {
        "instruction": "Run command immune to hangups",
        "command": "nohup ./long_script.sh > output.log 2>&1 &",
        "explanation": "Runs script in background, survives logout, logs output"
    },
    {
        "instruction": "Disown a running background job",
        "command": "disown -h %1",
        "explanation": "Makes job 1 immune to SIGHUP (survive logout)"
    },
    {
        "instruction": "Start screen session",
        "command": "screen -S sessionname",
        "explanation": "Creates named screen session for persistent terminal"
    },
    {
        "instruction": "Reattach to screen session",
        "command": "screen -r sessionname",
        "explanation": "Reattaches to existing screen session"
    },
    {
        "instruction": "List screen sessions",
        "command": "screen -ls",
        "explanation": "Lists all screen sessions"
    },
    {
        "instruction": "Start tmux session",
        "command": "tmux new -s sessionname",
        "explanation": "Creates named tmux session"
    },
    {
        "instruction": "Attach to tmux session",
        "command": "tmux attach -t sessionname",
        "explanation": "Attaches to existing tmux session"
    },
    {
        "instruction": "List tmux sessions",
        "command": "tmux ls",
        "explanation": "Lists all tmux sessions"
    },
    {
        "instruction": "Split text by delimiter",
        "command": "cut -d',' -f2 file.csv",
        "explanation": "Extracts second field from comma-delimited file"
    },
    {
        "instruction": "Join two files on common field",
        "command": "join -t',' file1.csv file2.csv",
        "explanation": "Joins files on first field, comma-delimited"
    },
    {
        "instruction": "Process JSON with jq",
        "command": "cat data.json | jq '.items[].name'",
        "explanation": "Extracts name from each item in JSON array"
    },
    {
        "instruction": "Pretty print JSON",
        "command": "cat data.json | jq '.'",
        "explanation": "Formats JSON with colors and indentation"
    },
    {
        "instruction": "Convert JSON to CSV",
        "command": "cat data.json | jq -r '.[] | [.id, .name] | @csv'",
        "explanation": "Converts JSON array to CSV format"
    },
    {
        "instruction": "Replace text with sed",
        "command": "sed 's/old/new/g' file.txt",
        "explanation": "Replaces all occurrences of old with new"
    },
    {
        "instruction": "Delete lines matching pattern",
        "command": "sed '/pattern/d' file.txt",
        "explanation": "Removes lines containing pattern"
    },
    {
        "instruction": "Insert line before match",
        "command": "sed '/pattern/i\\newline' file.txt",
        "explanation": "Inserts newline before lines matching pattern"
    },
    {
        "instruction": "Sum column of numbers",
        "command": "awk '{sum += $1} END {print sum}' file.txt",
        "explanation": "Sums first column and prints total"
    },
    {
        "instruction": "Calculate average of column",
        "command": "awk '{sum += $1; count++} END {print sum/count}' file.txt",
        "explanation": "Calculates average of first column"
    },
    {
        "instruction": "Print lines between patterns",
        "command": "awk '/start/,/end/' file.txt",
        "explanation": "Prints lines from start pattern to end pattern"
    },
    {
        "instruction": "Generate random password",
        "command": "openssl rand -base64 32 | tr -d '=' | head -c 24",
        "explanation": "Generates 24-character random password"
    },
    {
        "instruction": "Generate UUID",
        "command": "uuidgen",
        "explanation": "Generates a random UUID"
    },
    {
        "instruction": "Calculate file checksum",
        "command": "sha256sum filename",
        "explanation": "Calculates SHA-256 hash of file"
    },
    {
        "instruction": "Verify file checksum",
        "command": "sha256sum -c checksums.txt",
        "explanation": "Verifies files against checksum list"
    },
    {
        "instruction": "Encrypt a file",
        "command": "openssl enc -aes-256-cbc -salt -in file.txt -out file.enc",
        "explanation": "Encrypts file with AES-256, prompts for password"
    },
    {
        "instruction": "Decrypt a file",
        "command": "openssl enc -d -aes-256-cbc -in file.enc -out file.txt",
        "explanation": "Decrypts AES-encrypted file"
    },
    {
        "instruction": "Base64 encode",
        "command": "echo 'text' | base64",
        "explanation": "Encodes text in base64"
    },
    {
        "instruction": "Base64 decode",
        "command": "echo 'dGV4dAo=' | base64 -d",
        "explanation": "Decodes base64-encoded text"
    },
    {
        "instruction": "Compress file with gzip",
        "command": "gzip -k filename",
        "explanation": "Compresses file, -k keeps original"
    },
    {
        "instruction": "Compress file with best compression",
        "command": "gzip -9 -k filename",
        "explanation": "Uses best compression level"
    },
    {
        "instruction": "Decompress gzip file",
        "command": "gunzip filename.gz",
        "explanation": "Decompresses gzip file"
    },
    {
        "instruction": "View compressed file without extracting",
        "command": "zcat filename.gz | less",
        "explanation": "Views gzipped file contents directly"
    },
    {
        "instruction": "Search in compressed files",
        "command": "zgrep 'pattern' *.gz",
        "explanation": "Searches pattern in gzipped files"
    },
    {
        "instruction": "Parallel rsync for large transfers",
        "command": "rsync -avz --progress -e 'ssh -T -o Compression=no' source/ dest/",
        "explanation": "Optimized rsync over SSH for large files"
    },
    {
        "instruction": "Resume interrupted download",
        "command": "wget -c https://example.com/largefile.zip",
        "explanation": "Continues partial download with -c flag"
    },
    {
        "instruction": "Download with speed limit",
        "command": "wget --limit-rate=1m https://example.com/file.zip",
        "explanation": "Limits download to 1MB/s"
    },
    {
        "instruction": "Mirror website with wget",
        "command": "wget -m -k -p https://example.com",
        "explanation": "Mirrors site recursively, converts links, gets page requisites"
    },
    {
        "instruction": "Test HTTP response",
        "command": "curl -I https://example.com",
        "explanation": "Shows HTTP headers only"
    },
    {
        "instruction": "POST JSON with curl",
        "command": "curl -X POST -H 'Content-Type: application/json' -d '{\"key\":\"value\"}' https://api.example.com",
        "explanation": "Sends POST request with JSON body"
    },
    {
        "instruction": "Follow redirects with curl",
        "command": "curl -L https://example.com/redirect",
        "explanation": "Follows HTTP redirects"
    },
    {
        "instruction": "Show detailed curl timing",
        "command": "curl -w '@curl-format.txt' -o /dev/null -s https://example.com",
        "explanation": "Shows timing breakdown for request"
    },
]

SYSTEMD_TASKS = [
    {
        "instruction": "List all running services",
        "command": "systemctl list-units --type=service --state=running",
        "explanation": "Lists only running services"
    },
    {
        "instruction": "Start a service",
        "command": "sudo systemctl start nginx",
        "explanation": "Starts the nginx service"
    },
    {
        "instruction": "Stop a service",
        "command": "sudo systemctl stop nginx",
        "explanation": "Stops the nginx service"
    },
    {
        "instruction": "Restart a service",
        "command": "sudo systemctl restart nginx",
        "explanation": "Restarts the nginx service"
    },
    {
        "instruction": "Enable service at boot",
        "command": "sudo systemctl enable nginx",
        "explanation": "Enables nginx to start automatically at boot"
    },
    {
        "instruction": "Check service status",
        "command": "systemctl status nginx",
        "explanation": "Shows current status and recent logs for nginx"
    },
    {
        "instruction": "View service logs",
        "command": "journalctl -u nginx -f",
        "explanation": "Follows logs for nginx service"
    },
    {
        "instruction": "Reload service configuration",
        "command": "sudo systemctl reload nginx",
        "explanation": "Reloads config without full restart (if supported)"
    },
    {
        "instruction": "Show service dependencies",
        "command": "systemctl list-dependencies nginx",
        "explanation": "Shows dependency tree for nginx"
    },
    {
        "instruction": "Check why service failed",
        "command": "systemctl status nginx && journalctl -xe -u nginx",
        "explanation": "Shows status and detailed logs for failed service"
    },
    # NEW: Additional systemd tasks
    {
        "instruction": "Disable service at boot",
        "command": "sudo systemctl disable nginx",
        "explanation": "Prevents nginx from starting at boot"
    },
    {
        "instruction": "Enable and start service in one command",
        "command": "sudo systemctl enable --now nginx",
        "explanation": "Enables at boot and starts immediately"
    },
    {
        "instruction": "Mask a service (prevent from starting)",
        "command": "sudo systemctl mask nginx",
        "explanation": "Completely prevents service from starting, even manually"
    },
    {
        "instruction": "Unmask a service",
        "command": "sudo systemctl unmask nginx",
        "explanation": "Removes mask, allowing service to be started"
    },
    {
        "instruction": "List all failed services",
        "command": "systemctl --failed",
        "explanation": "Shows all services in failed state"
    },
    {
        "instruction": "Reset failed service state",
        "command": "sudo systemctl reset-failed nginx",
        "explanation": "Clears failed state for a service"
    },
    {
        "instruction": "Show service unit file",
        "command": "systemctl cat nginx",
        "explanation": "Displays the service unit file contents"
    },
    {
        "instruction": "Edit service unit file",
        "command": "sudo systemctl edit nginx",
        "explanation": "Creates override file for service customization"
    },
    {
        "instruction": "Edit service unit file (full)",
        "command": "sudo systemctl edit --full nginx",
        "explanation": "Edits full service file (creates copy)"
    },
    {
        "instruction": "Reload systemd daemon",
        "command": "sudo systemctl daemon-reload",
        "explanation": "Reloads systemd after unit file changes"
    },
    {
        "instruction": "Show service properties",
        "command": "systemctl show nginx",
        "explanation": "Shows all properties of the service unit"
    },
    {
        "instruction": "Check if service is active",
        "command": "systemctl is-active nginx",
        "explanation": "Returns active/inactive status"
    },
    {
        "instruction": "Check if service is enabled",
        "command": "systemctl is-enabled nginx",
        "explanation": "Returns enabled/disabled status"
    },
    {
        "instruction": "List all available services",
        "command": "systemctl list-unit-files --type=service",
        "explanation": "Lists all service unit files and their state"
    },
    {
        "instruction": "Show reverse dependencies",
        "command": "systemctl list-dependencies --reverse nginx",
        "explanation": "Shows what depends on this service"
    },
    {
        "instruction": "View logs since boot",
        "command": "journalctl -u nginx -b",
        "explanation": "Shows logs for service since current boot"
    },
    {
        "instruction": "View logs from specific time",
        "command": "journalctl -u nginx --since '1 hour ago'",
        "explanation": "Shows service logs from the last hour"
    },
    {
        "instruction": "View logs with priority filter",
        "command": "journalctl -u nginx -p err",
        "explanation": "Shows only error-level and above logs"
    },
    {
        "instruction": "Export logs to file",
        "command": "journalctl -u nginx > nginx_logs.txt",
        "explanation": "Exports service logs to text file"
    },
    {
        "instruction": "Show disk usage of journal",
        "command": "journalctl --disk-usage",
        "explanation": "Shows how much disk space logs consume"
    },
    {
        "instruction": "Clean old journal entries",
        "command": "sudo journalctl --vacuum-time=7d",
        "explanation": "Removes journal entries older than 7 days"
    },
    {
        "instruction": "Clean journal to size limit",
        "command": "sudo journalctl --vacuum-size=500M",
        "explanation": "Reduces journal size to 500MB"
    },
    {
        "instruction": "List all systemd timers",
        "command": "systemctl list-timers",
        "explanation": "Shows all active systemd timers (scheduled tasks)"
    },
    {
        "instruction": "List all targets",
        "command": "systemctl list-units --type=target",
        "explanation": "Shows all system targets (like runlevels)"
    },
    {
        "instruction": "Get default target",
        "command": "systemctl get-default",
        "explanation": "Shows the default boot target"
    },
    {
        "instruction": "Set default target to multi-user",
        "command": "sudo systemctl set-default multi-user.target",
        "explanation": "Sets system to boot to CLI (no GUI)"
    },
    {
        "instruction": "Set default target to graphical",
        "command": "sudo systemctl set-default graphical.target",
        "explanation": "Sets system to boot with GUI"
    },
    {
        "instruction": "Switch to different target",
        "command": "sudo systemctl isolate multi-user.target",
        "explanation": "Immediately switches to multi-user target"
    },
    {
        "instruction": "Show boot time analysis",
        "command": "systemd-analyze blame",
        "explanation": "Shows which services took longest to start"
    },
    {
        "instruction": "Show boot critical chain",
        "command": "systemd-analyze critical-chain",
        "explanation": "Shows the critical path of boot process"
    },
    {
        "instruction": "Generate boot chart",
        "command": "systemd-analyze plot > boot_chart.svg",
        "explanation": "Creates SVG visualization of boot process"
    },
    {
        "instruction": "Verify unit file syntax",
        "command": "systemd-analyze verify /etc/systemd/system/myservice.service",
        "explanation": "Checks unit file for errors"
    },
    {
        "instruction": "Show system state",
        "command": "systemctl status",
        "explanation": "Shows overall system state and running/failed units"
    },
    {
        "instruction": "Reboot the system",
        "command": "sudo systemctl reboot",
        "explanation": "Reboots the system through systemd"
    },
    {
        "instruction": "Power off the system",
        "command": "sudo systemctl poweroff",
        "explanation": "Powers off the system through systemd"
    },
    {
        "instruction": "Suspend the system",
        "command": "sudo systemctl suspend",
        "explanation": "Suspends system to RAM"
    },
    {
        "instruction": "Hibernate the system",
        "command": "sudo systemctl hibernate",
        "explanation": "Hibernates system to disk"
    },
    {
        "instruction": "Show host information",
        "command": "hostnamectl",
        "explanation": "Shows hostname, OS, kernel, and architecture info"
    },
    {
        "instruction": "Set hostname",
        "command": "sudo hostnamectl set-hostname newhostname",
        "explanation": "Sets the system hostname persistently"
    },
    {
        "instruction": "Show locale settings",
        "command": "localectl",
        "explanation": "Shows system locale and keyboard settings"
    },
    {
        "instruction": "Show time settings",
        "command": "timedatectl",
        "explanation": "Shows time zone, NTP status, and time info"
    },
    {
        "instruction": "Set timezone",
        "command": "sudo timedatectl set-timezone America/New_York",
        "explanation": "Sets system timezone"
    },
    {
        "instruction": "Enable NTP synchronization",
        "command": "sudo timedatectl set-ntp true",
        "explanation": "Enables automatic time synchronization"
    },
]

NETWORKING_TASKS = [
    {
        "instruction": "Show IP addresses",
        "command": "ip addr show",
        "explanation": "Shows all network interfaces and their IP addresses"
    },
    {
        "instruction": "Show routing table",
        "command": "ip route show",
        "explanation": "Displays routing table"
    },
    {
        "instruction": "Test network connectivity",
        "command": "ping -c 4 google.com",
        "explanation": "Sends 4 ICMP packets to test connectivity"
    },
    {
        "instruction": "Check DNS resolution",
        "command": "dig google.com",
        "explanation": "Performs DNS lookup with detailed information"
    },
    {
        "instruction": "Show open ports and listening services",
        "command": "ss -tuln",
        "explanation": "Shows TCP/UDP ports in listening state"
    },
    {
        "instruction": "Trace route to host",
        "command": "traceroute google.com",
        "explanation": "Shows network path to destination"
    },
    {
        "instruction": "Download file from URL",
        "command": "curl -O https://example.com/file.zip",
        "explanation": "Downloads file preserving remote filename"
    },
    {
        "instruction": "Check firewall status",
        "command": "sudo ufw status verbose",
        "explanation": "Shows UFW firewall rules and status"
    },
    {
        "instruction": "Add firewall rule",
        "command": "sudo ufw allow 22/tcp",
        "explanation": "Allows incoming TCP connections on port 22"
    },
    {
        "instruction": "Test if port is open",
        "command": "nc -zv hostname 80",
        "explanation": "Tests TCP connection to port 80"
    },
    # NEW: Additional networking tasks
    {
        "instruction": "Show all network connections",
        "command": "ss -tunap",
        "explanation": "Shows all TCP/UDP connections with process names"
    },
    {
        "instruction": "Show network statistics",
        "command": "ss -s",
        "explanation": "Shows summary of network statistics"
    },
    {
        "instruction": "Show established connections only",
        "command": "ss -t state established",
        "explanation": "Lists only established TCP connections"
    },
    {
        "instruction": "Add static IP address",
        "command": "sudo ip addr add 192.168.1.100/24 dev eth0",
        "explanation": "Adds IP address to interface (non-persistent)"
    },
    {
        "instruction": "Remove IP address",
        "command": "sudo ip addr del 192.168.1.100/24 dev eth0",
        "explanation": "Removes IP address from interface"
    },
    {
        "instruction": "Bring interface up",
        "command": "sudo ip link set eth0 up",
        "explanation": "Activates network interface"
    },
    {
        "instruction": "Bring interface down",
        "command": "sudo ip link set eth0 down",
        "explanation": "Deactivates network interface"
    },
    {
        "instruction": "Add default gateway",
        "command": "sudo ip route add default via 192.168.1.1",
        "explanation": "Sets default gateway"
    },
    {
        "instruction": "Add static route",
        "command": "sudo ip route add 10.0.0.0/8 via 192.168.1.254",
        "explanation": "Adds route for 10.x.x.x via specific gateway"
    },
    {
        "instruction": "Delete route",
        "command": "sudo ip route del 10.0.0.0/8",
        "explanation": "Removes routing entry"
    },
    {
        "instruction": "Show ARP cache",
        "command": "ip neigh show",
        "explanation": "Displays ARP/neighbor cache"
    },
    {
        "instruction": "Flush ARP cache",
        "command": "sudo ip neigh flush all",
        "explanation": "Clears all ARP cache entries"
    },
    {
        "instruction": "Simple DNS lookup",
        "command": "nslookup google.com",
        "explanation": "Basic DNS query"
    },
    {
        "instruction": "Query specific DNS server",
        "command": "dig @8.8.8.8 google.com",
        "explanation": "Queries Google's DNS specifically"
    },
    {
        "instruction": "Reverse DNS lookup",
        "command": "dig -x 8.8.8.8",
        "explanation": "Looks up hostname for IP address"
    },
    {
        "instruction": "Get MX records",
        "command": "dig google.com MX",
        "explanation": "Gets mail exchanger records"
    },
    {
        "instruction": "Get all DNS records",
        "command": "dig google.com ANY",
        "explanation": "Queries all DNS record types"
    },
    {
        "instruction": "Check DNS configuration",
        "command": "cat /etc/resolv.conf",
        "explanation": "Shows configured DNS servers"
    },
    {
        "instruction": "Test DNS resolution with host",
        "command": "host google.com",
        "explanation": "Simple DNS lookup using host command"
    },
    {
        "instruction": "Flush DNS cache (systemd)",
        "command": "sudo systemd-resolve --flush-caches",
        "explanation": "Clears systemd-resolved DNS cache"
    },
    {
        "instruction": "Enable UFW firewall",
        "command": "sudo ufw enable",
        "explanation": "Enables UFW firewall"
    },
    {
        "instruction": "Disable UFW firewall",
        "command": "sudo ufw disable",
        "explanation": "Disables UFW firewall"
    },
    {
        "instruction": "Allow incoming on port range",
        "command": "sudo ufw allow 8000:8100/tcp",
        "explanation": "Allows TCP ports 8000-8100"
    },
    {
        "instruction": "Allow from specific IP",
        "command": "sudo ufw allow from 192.168.1.100",
        "explanation": "Allows all traffic from specific IP"
    },
    {
        "instruction": "Allow from subnet to port",
        "command": "sudo ufw allow from 192.168.1.0/24 to any port 22",
        "explanation": "Allows SSH only from specific subnet"
    },
    {
        "instruction": "Deny specific IP",
        "command": "sudo ufw deny from 192.168.1.100",
        "explanation": "Blocks all traffic from IP"
    },
    {
        "instruction": "Delete UFW rule by number",
        "command": "sudo ufw delete 3",
        "explanation": "Deletes rule number 3 (use 'ufw status numbered' first)"
    },
    {
        "instruction": "Reset UFW to defaults",
        "command": "sudo ufw reset",
        "explanation": "Removes all rules and resets to defaults"
    },
    {
        "instruction": "List iptables rules",
        "command": "sudo iptables -L -n -v",
        "explanation": "Shows all iptables rules with packet counts"
    },
    {
        "instruction": "Add iptables rule",
        "command": "sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT",
        "explanation": "Allows incoming HTTP traffic"
    },
    {
        "instruction": "Block incoming IP with iptables",
        "command": "sudo iptables -A INPUT -s 192.168.1.100 -j DROP",
        "explanation": "Blocks all traffic from specific IP"
    },
    {
        "instruction": "Save iptables rules",
        "command": "sudo iptables-save > /etc/iptables/rules.v4",
        "explanation": "Saves current rules to persist on reboot"
    },
    {
        "instruction": "Show network interface statistics",
        "command": "ip -s link",
        "explanation": "Shows packet/byte statistics per interface"
    },
    {
        "instruction": "Show detailed interface info",
        "command": "ethtool eth0",
        "explanation": "Shows detailed NIC information"
    },
    {
        "instruction": "Set interface MTU",
        "command": "sudo ip link set eth0 mtu 9000",
        "explanation": "Sets jumbo frames on interface"
    },
    {
        "instruction": "Show WiFi networks",
        "command": "nmcli device wifi list",
        "explanation": "Lists available WiFi networks"
    },
    {
        "instruction": "Connect to WiFi",
        "command": "nmcli device wifi connect SSID password 'password'",
        "explanation": "Connects to WiFi network"
    },
    {
        "instruction": "Show network connections (NetworkManager)",
        "command": "nmcli connection show",
        "explanation": "Lists all configured connections"
    },
    {
        "instruction": "Restart networking",
        "command": "sudo systemctl restart NetworkManager",
        "explanation": "Restarts NetworkManager service"
    },
    {
        "instruction": "Capture packets on interface",
        "command": "sudo tcpdump -i eth0 -c 100",
        "explanation": "Captures 100 packets on interface"
    },
    {
        "instruction": "Capture packets to file",
        "command": "sudo tcpdump -i eth0 -w capture.pcap",
        "explanation": "Saves packet capture to file for Wireshark"
    },
    {
        "instruction": "Capture specific port traffic",
        "command": "sudo tcpdump -i eth0 port 80",
        "explanation": "Captures only HTTP traffic"
    },
    {
        "instruction": "Capture with host filter",
        "command": "sudo tcpdump -i eth0 host 192.168.1.100",
        "explanation": "Captures traffic to/from specific host"
    },
    {
        "instruction": "Check which process uses a port",
        "command": "sudo lsof -i :443",
        "explanation": "Shows process using port 443"
    },
    {
        "instruction": "Show network bandwidth usage",
        "command": "iftop -i eth0",
        "explanation": "Real-time bandwidth monitor per connection"
    },
    {
        "instruction": "Show bandwidth by process",
        "command": "nethogs eth0",
        "explanation": "Shows bandwidth usage per process"
    },
    {
        "instruction": "Test connection bandwidth",
        "command": "iperf3 -c server_ip",
        "explanation": "Tests network throughput to iperf server"
    },
    {
        "instruction": "Start iperf server",
        "command": "iperf3 -s",
        "explanation": "Starts iperf server for bandwidth testing"
    },
    {
        "instruction": "Check public IP",
        "command": "curl ifconfig.me",
        "explanation": "Shows your public IP address"
    },
    {
        "instruction": "Check public IP with details",
        "command": "curl ipinfo.io",
        "explanation": "Shows public IP with geolocation info"
    },
    {
        "instruction": "Test HTTP endpoint",
        "command": "curl -v https://api.example.com/health",
        "explanation": "Verbose HTTP request showing headers"
    },
    {
        "instruction": "Send HTTP POST request",
        "command": "curl -X POST -d 'data=value' https://api.example.com",
        "explanation": "Sends form-encoded POST data"
    },
    {
        "instruction": "Test SSL certificate",
        "command": "openssl s_client -connect example.com:443 -servername example.com",
        "explanation": "Shows SSL certificate details"
    },
    {
        "instruction": "Check certificate expiration",
        "command": "echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates",
        "explanation": "Shows certificate validity dates"
    },
    {
        "instruction": "Create SSH tunnel",
        "command": "ssh -L 8080:localhost:80 user@remote",
        "explanation": "Forwards local 8080 to remote localhost:80"
    },
    {
        "instruction": "Create reverse SSH tunnel",
        "command": "ssh -R 8080:localhost:80 user@remote",
        "explanation": "Exposes local port on remote server"
    },
    {
        "instruction": "Create SOCKS proxy",
        "command": "ssh -D 1080 user@remote",
        "explanation": "Creates SOCKS proxy through SSH"
    },
]

PACKAGE_MANAGEMENT_TASKS = [
    {
        "instruction": "Update package lists",
        "command": "sudo apt update",
        "explanation": "Updates available package information (Debian/Ubuntu)"
    },
    {
        "instruction": "Upgrade all packages",
        "command": "sudo apt upgrade -y",
        "explanation": "Upgrades all packages to latest versions"
    },
    {
        "instruction": "Install a package",
        "command": "sudo apt install nginx -y",
        "explanation": "Installs nginx package"
    },
    {
        "instruction": "Remove a package",
        "command": "sudo apt remove nginx",
        "explanation": "Removes nginx but keeps config files"
    },
    {
        "instruction": "Completely remove package with configs",
        "command": "sudo apt purge nginx",
        "explanation": "Removes nginx and its configuration files"
    },
    {
        "instruction": "Search for packages",
        "command": "apt search nginx",
        "explanation": "Searches package repositories for nginx"
    },
    {
        "instruction": "Show package information",
        "command": "apt show nginx",
        "explanation": "Displays detailed package information"
    },
    {
        "instruction": "List installed packages",
        "command": "dpkg -l",
        "explanation": "Lists all installed packages"
    },
    {
        "instruction": "Clean package cache",
        "command": "sudo apt autoremove && sudo apt clean",
        "explanation": "Removes unused packages and clears cache"
    },
    # NEW: Additional package management tasks
    {
        "instruction": "Full system upgrade",
        "command": "sudo apt full-upgrade -y",
        "explanation": "Upgrades with smart conflict resolution"
    },
    {
        "instruction": "Dist upgrade to new release",
        "command": "sudo apt dist-upgrade",
        "explanation": "Handles changed dependencies during upgrades"
    },
    {
        "instruction": "Check for broken packages",
        "command": "sudo apt --fix-broken install",
        "explanation": "Fixes broken package dependencies"
    },
    {
        "instruction": "Show package dependencies",
        "command": "apt depends nginx",
        "explanation": "Shows what packages nginx depends on"
    },
    {
        "instruction": "Show reverse dependencies",
        "command": "apt rdepends nginx",
        "explanation": "Shows what packages depend on nginx"
    },
    {
        "instruction": "List packages by size",
        "command": "dpkg-query -W --showformat='${Installed-Size}\\t${Package}\\n' | sort -rn | head -20",
        "explanation": "Lists largest installed packages"
    },
    {
        "instruction": "Check if package is installed",
        "command": "dpkg -l | grep nginx",
        "explanation": "Shows if nginx is installed"
    },
    {
        "instruction": "Show files installed by package",
        "command": "dpkg -L nginx",
        "explanation": "Lists all files installed by package"
    },
    {
        "instruction": "Find which package owns a file",
        "command": "dpkg -S /usr/bin/nginx",
        "explanation": "Shows which package installed a file"
    },
    {
        "instruction": "Hold package version",
        "command": "sudo apt-mark hold nginx",
        "explanation": "Prevents package from being upgraded"
    },
    {
        "instruction": "Unhold package",
        "command": "sudo apt-mark unhold nginx",
        "explanation": "Allows package to be upgraded again"
    },
    {
        "instruction": "Show held packages",
        "command": "apt-mark showhold",
        "explanation": "Lists all held packages"
    },
    {
        "instruction": "Download package without installing",
        "command": "apt download nginx",
        "explanation": "Downloads .deb file without installation"
    },
    {
        "instruction": "Install .deb file",
        "command": "sudo dpkg -i package.deb",
        "explanation": "Installs local .deb file"
    },
    {
        "instruction": "Install .deb with dependencies",
        "command": "sudo apt install ./package.deb",
        "explanation": "Installs .deb and resolves dependencies"
    },
    {
        "instruction": "Reconfigure package",
        "command": "sudo dpkg-reconfigure tzdata",
        "explanation": "Re-runs package configuration"
    },
    {
        "instruction": "List manually installed packages",
        "command": "apt-mark showmanual",
        "explanation": "Shows packages installed manually (not as deps)"
    },
    {
        "instruction": "Mark package as auto-installed",
        "command": "sudo apt-mark auto nginx",
        "explanation": "Marks as auto-installed (will be autoremoved)"
    },
    {
        "instruction": "Add PPA repository",
        "command": "sudo add-apt-repository ppa:nginx/stable",
        "explanation": "Adds PPA for newer nginx versions"
    },
    {
        "instruction": "Remove PPA repository",
        "command": "sudo add-apt-repository --remove ppa:nginx/stable",
        "explanation": "Removes PPA from sources"
    },
    {
        "instruction": "List all repositories",
        "command": "grep -rh ^deb /etc/apt/sources.list*",
        "explanation": "Shows all configured apt repositories"
    },
    {
        "instruction": "Update package from specific repo",
        "command": "sudo apt install -t stable nginx",
        "explanation": "Installs from specific release"
    },
    {
        "instruction": "List available versions of package",
        "command": "apt policy nginx",
        "explanation": "Shows available versions and sources"
    },
    {
        "instruction": "Install specific version",
        "command": "sudo apt install nginx=1.18.0-0ubuntu1",
        "explanation": "Installs specific version of package"
    },
    {
        "instruction": "Downgrade package",
        "command": "sudo apt install nginx=1.17.0-0ubuntu1",
        "explanation": "Installs older version to downgrade"
    },
    # Red Hat / Fedora / CentOS commands
    {
        "instruction": "Install package (yum)",
        "command": "sudo yum install nginx -y",
        "explanation": "Installs nginx on Red Hat/CentOS systems"
    },
    {
        "instruction": "Install package (dnf)",
        "command": "sudo dnf install nginx -y",
        "explanation": "Installs nginx on Fedora/RHEL 8+"
    },
    {
        "instruction": "Update all packages (yum)",
        "command": "sudo yum update -y",
        "explanation": "Updates all packages on Red Hat systems"
    },
    {
        "instruction": "Update all packages (dnf)",
        "command": "sudo dnf upgrade -y",
        "explanation": "Updates all packages on Fedora systems"
    },
    {
        "instruction": "Search packages (dnf)",
        "command": "dnf search nginx",
        "explanation": "Searches for packages on Fedora/RHEL"
    },
    {
        "instruction": "Show package info (dnf)",
        "command": "dnf info nginx",
        "explanation": "Shows package details on Fedora/RHEL"
    },
    {
        "instruction": "List installed packages (rpm)",
        "command": "rpm -qa",
        "explanation": "Lists all installed RPM packages"
    },
    {
        "instruction": "Find package owner (rpm)",
        "command": "rpm -qf /usr/bin/nginx",
        "explanation": "Shows which RPM owns a file"
    },
    {
        "instruction": "List files in package (rpm)",
        "command": "rpm -ql nginx",
        "explanation": "Lists files installed by RPM package"
    },
    {
        "instruction": "Install from EPEL",
        "command": "sudo dnf install epel-release && sudo dnf install htop",
        "explanation": "Enables EPEL and installs package from it"
    },
    # Arch Linux commands
    {
        "instruction": "Install package (pacman)",
        "command": "sudo pacman -S nginx",
        "explanation": "Installs nginx on Arch Linux"
    },
    {
        "instruction": "Update system (pacman)",
        "command": "sudo pacman -Syu",
        "explanation": "Syncs repos and updates all packages"
    },
    {
        "instruction": "Search packages (pacman)",
        "command": "pacman -Ss nginx",
        "explanation": "Searches for packages in Arch repos"
    },
    {
        "instruction": "Remove package (pacman)",
        "command": "sudo pacman -R nginx",
        "explanation": "Removes package on Arch Linux"
    },
    {
        "instruction": "Remove package with dependencies (pacman)",
        "command": "sudo pacman -Rs nginx",
        "explanation": "Removes package and unused dependencies"
    },
    # Snap and Flatpak
    {
        "instruction": "Install snap package",
        "command": "sudo snap install code --classic",
        "explanation": "Installs VS Code via snap"
    },
    {
        "instruction": "List installed snaps",
        "command": "snap list",
        "explanation": "Shows all installed snap packages"
    },
    {
        "instruction": "Update all snaps",
        "command": "sudo snap refresh",
        "explanation": "Updates all snap packages"
    },
    {
        "instruction": "Remove snap package",
        "command": "sudo snap remove code",
        "explanation": "Removes snap package"
    },
    {
        "instruction": "Install flatpak application",
        "command": "flatpak install flathub org.mozilla.firefox",
        "explanation": "Installs Firefox via Flatpak"
    },
    {
        "instruction": "List flatpak applications",
        "command": "flatpak list",
        "explanation": "Shows installed Flatpak apps"
    },
    {
        "instruction": "Update flatpak applications",
        "command": "flatpak update",
        "explanation": "Updates all Flatpak applications"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up a new Linux web server",
        "steps": [
            "Update system packages: apt update && apt upgrade -y",
            "Install nginx: apt install nginx -y",
            "Start and enable nginx: systemctl enable --now nginx",
            "Configure firewall: ufw allow 'Nginx Full'",
            "Create web directory: mkdir -p /var/www/mysite",
            "Configure nginx virtual host",
            "Set proper permissions: chown -R www-data:www-data /var/www/mysite",
            "Test configuration: nginx -t",
            "Reload nginx: systemctl reload nginx",
            "Verify site is accessible"
        ]
    },
    {
        "instruction": "Diagnose high CPU usage on server",
        "steps": [
            "Check overall load: uptime and top",
            "Identify high-CPU processes: top -o %CPU or htop",
            "Check if it's system or user processes",
            "Review process details: ps aux | grep <process>",
            "Check for runaway processes or infinite loops",
            "Review application logs for errors",
            "Check for cron jobs or scheduled tasks",
            "Use strace to trace system calls if needed",
            "Consider using perf for detailed profiling"
        ]
    },
    {
        "instruction": "Set up SSH key authentication and disable password login",
        "steps": [
            "Generate SSH key pair on client: ssh-keygen -t ed25519",
            "Copy public key to server: ssh-copy-id user@server",
            "Test key-based login",
            "Backup sshd_config: cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak",
            "Edit /etc/ssh/sshd_config",
            "Set PasswordAuthentication no",
            "Set PubkeyAuthentication yes",
            "Optionally set PermitRootLogin no",
            "Test config: sshd -t",
            "Restart SSH: systemctl restart sshd",
            "Verify you can still login before disconnecting"
        ]
    },
    {
        "instruction": "Set up automatic backups with cron",
        "steps": [
            "Create backup script in /usr/local/bin/backup.sh",
            "Make script executable: chmod +x /usr/local/bin/backup.sh",
            "Test script manually first",
            "Edit crontab: crontab -e",
            "Add schedule: 0 2 * * * /usr/local/bin/backup.sh",
            "Verify cron job: crontab -l",
            "Check cron service: systemctl status cron",
            "Set up log rotation for backup logs",
            "Test email notifications if configured"
        ]
    },
    {
        "instruction": "Troubleshoot a service that won't start",
        "steps": [
            "Check service status: systemctl status service-name",
            "View detailed logs: journalctl -xe -u service-name",
            "Check config syntax if applicable",
            "Verify dependencies: systemctl list-dependencies service-name",
            "Check file permissions on config and data directories",
            "Verify port is not already in use: ss -tuln | grep port",
            "Check SELinux/AppArmor if enabled",
            "Try starting manually for verbose output",
            "Review system resource availability (memory, disk)",
            "Check for core dumps: coredumpctl list"
        ]
    },
    {
        "instruction": "Set up a new user with sudo access",
        "steps": [
            "Create user: useradd -m -s /bin/bash username",
            "Set password: passwd username",
            "Add to sudo group: usermod -aG sudo username",
            "Or edit sudoers: visudo (add 'username ALL=(ALL:ALL) ALL')",
            "Test sudo access: su - username && sudo whoami",
            "Set up SSH keys for user",
            "Configure user's shell environment",
            "Add to necessary groups for file access"
        ]
    },
    {
        "instruction": "Secure a Linux server (basic hardening)",
        "steps": [
            "Update all packages: apt update && apt upgrade",
            "Configure firewall (UFW or iptables)",
            "Disable root SSH login",
            "Use SSH key authentication only",
            "Change SSH port (optional)",
            "Install fail2ban for brute-force protection",
            "Set up unattended-upgrades for security updates",
            "Disable unnecessary services",
            "Configure audit logging",
            "Set up monitoring and alerts"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is the difference between sudo and su?",
        "answer": "sudo executes a single command as root (or another user), prompting for YOUR password and logging the action. It's configurable via /etc/sudoers. su switches your entire session to another user (root by default), prompting for THEIR password. sudo is preferred because: it has better logging, doesn't require sharing root password, can be more granularly controlled, and limits privilege escalation to specific commands."
    },
    {
        "question": "What are Linux file permissions?",
        "answer": "Linux has three permission types: read (r=4), write (w=2), execute (x=1), for three categories: owner, group, others. Displayed as rwxrwxrwx (e.g., -rwxr-xr-x = 755). chmod changes permissions: chmod 755 file or chmod u+x file. chown changes ownership: chown user:group file. Special permissions: setuid (4), setgid (2), sticky bit (1). Directories need execute permission to be entered."
    },
    {
        "question": "What is a Linux process?",
        "answer": "A process is a running program instance with its own memory space, PID, and resources. Processes have states: Running, Sleeping, Stopped, Zombie. Every process has a parent (PPID); init/systemd (PID 1) is the root. Signals control processes: SIGTERM (15) for graceful stop, SIGKILL (9) for forced kill. View with ps, top, htop. Background processes run with & or nohup."
    },
    {
        "question": "What is systemd?",
        "answer": "systemd is the modern init system and service manager for Linux. It replaces SysV init with parallel startup for faster boot. Key concepts: Units (services, targets, mounts, etc.), Targets (group units, like runlevels), Journal (centralized logging). Commands: systemctl for service management, journalctl for logs. Unit files in /etc/systemd/system/ or /lib/systemd/system/. It handles dependencies, socket activation, and resource control."
    },
    {
        "question": "What is the PATH environment variable?",
        "answer": "PATH is a colon-separated list of directories where the shell searches for commands. When you type a command, the shell searches PATH directories in order. View with echo $PATH. Add directories: export PATH=$PATH:/new/path. Permanent changes go in ~/.bashrc or ~/.profile. Security tip: Never put current directory (.) at the start of PATH, as it could run malicious scripts."
    },
    {
        "question": "What's the difference between hard links and soft links?",
        "answer": "Hard links point directly to file data (inode); the original and link are indistinguishable. Deleting one doesn't affect the other. Can't cross filesystems or link directories. Soft/symbolic links point to a path (filename); they break if the target is moved/deleted. Can cross filesystems and link directories. Create with ln (hard) or ln -s (soft). ls -l shows soft links with -> pointing to target."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "How does Linux memory management work?",
        "answer": "Linux uses virtual memory with demand paging. Physical RAM is divided into pages (usually 4KB). The kernel manages: Page cache (caches file data), Buffer cache (block device data), Swap (overflow to disk). Memory states: Used, Free, Cached (can be reclaimed), Buffers. The OOM killer terminates processes if memory is exhausted. Commands: free -h shows memory, vmstat shows virtual memory stats, /proc/meminfo has details. 'Available' memory includes reclaimable cache."
    },
    {
        "question": "What is the Linux kernel and how do modules work?",
        "answer": "The kernel is the core of Linux, managing hardware, processes, memory, and security. It runs in privileged mode (kernel space). Modules are loadable kernel extensions (.ko files) that add functionality without recompiling. Commands: lsmod lists loaded modules, modprobe loads modules with dependencies, rmmod removes modules. Module configs in /etc/modprobe.d/. The kernel exposes info through /proc (processes, system) and /sys (devices, drivers)."
    },
    {
        "question": "How do cgroups and namespaces work?",
        "answer": "cgroups (control groups) limit and isolate resource usage (CPU, memory, I/O) for process groups. Used by systemd and containers. Namespaces isolate what processes can see: PID (process IDs), NET (networking), MNT (mounts), UTS (hostname), IPC (inter-process comm), USER (user IDs). Containers combine both: namespaces for isolation, cgroups for resource limits. This is how Docker/Podman work without full VMs."
    },
    {
        "question": "How does the Linux boot process work?",
        "answer": "1) BIOS/UEFI initializes hardware, loads bootloader. 2) Bootloader (GRUB2) loads kernel and initramfs. 3) Kernel initializes, mounts initramfs as temporary root. 4) initramfs loads needed drivers, switches to real root filesystem. 5) Kernel starts init system (systemd, PID 1). 6) systemd starts services according to target (graphical.target, multi-user.target). GRUB config in /boot/grub/grub.cfg, systemd targets control what services run."
    },
    {
        "question": "What is SELinux/AppArmor and when should I use it?",
        "answer": "SELinux and AppArmor are Mandatory Access Control (MAC) systems adding security beyond traditional permissions. SELinux (Red Hat family) uses labels on files and processes with complex policies. AppArmor (Ubuntu/Debian) uses path-based profiles, simpler to configure. Both can: confine services to only access required resources, prevent privilege escalation, limit damage from compromised services. Check with getenforce (SELinux) or aa-status (AppArmor). Learning curve is steep but worth it for servers."
    },
    {
        "question": "How does Linux networking stack work?",
        "answer": "Linux networking follows the OSI model implementation: netfilter (firewall), routing tables, network namespaces. Key components: Network interfaces (eth0, lo), IP addresses/routes, iptables/nftables (packet filtering), TCP/UDP stacks. Configuration: ip command (modern), ifconfig/route (legacy), /etc/network/interfaces or NetworkManager. Bridging creates virtual switches, VLAN tagging for network segmentation, bonding for redundancy/bandwidth."
    },
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "Run rm -rf / to clean up the system",
        "error_type": "dangerous_operation",
        "response": {
            "status": "blocked",
            "severity": "critical",
            "message": "STOP - This will destroy your entire system",
            "explanation": "rm -rf / recursively deletes everything from root. Modern rm requires --no-preserve-root to actually execute this, but NEVER run it. This would delete: all user data, all programs, the operating system itself.",
            "safe_alternatives": [
                "Clean package cache: apt clean",
                "Remove old kernels: apt autoremove",
                "Find large files: du -sh /* | sort -rh | head",
                "Clear logs: journalctl --vacuum-time=7d"
            ]
        }
    },
    {
        "instruction": "I ran a command and got 'Permission denied'",
        "error_type": "permissions",
        "response": {
            "status": "recoverable",
            "common_causes": [
                "Command requires root/sudo privileges",
                "File ownership doesn't allow access",
                "Execute permission missing on script",
                "SELinux/AppArmor blocking access"
            ],
            "solutions": [
                "Try with sudo: sudo command",
                "Check permissions: ls -la file",
                "Check ownership: stat file",
                "Add execute permission: chmod +x script.sh",
                "Check SELinux: getenforce && ausearch -m avc -ts recent"
            ],
            "investigation": "Run: namei -l /path/to/file to see permission chain"
        }
    },
    {
        "instruction": "My server ran out of disk space",
        "error_type": "resource_exhaustion",
        "response": {
            "status": "needs_action",
            "immediate_steps": [
                "Check usage: df -h",
                "Find large directories: du -sh /* | sort -rh | head",
                "Check for large files: find / -xdev -type f -size +100M 2>/dev/null"
            ],
            "common_culprits": [
                "/var/log - rotated logs piling up",
                "/tmp - temporary files not cleaned",
                "/var/lib/docker - container storage",
                "/home - user files",
                "Core dumps filling disk"
            ],
            "cleanup_commands": [
                "Clear old logs: journalctl --vacuum-size=500M",
                "Remove old packages: apt autoremove && apt clean",
                "Clean docker: docker system prune -a",
                "Find and remove old files: find /tmp -type f -mtime +7 -delete"
            ]
        }
    },
    {
        "instruction": "SSH connection is being refused",
        "error_type": "network",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check if sshd is running: systemctl status sshd",
                "Verify listening port: ss -tuln | grep 22",
                "Check firewall: ufw status or iptables -L",
                "Test local connection: ssh localhost",
                "Check SSH config: cat /etc/ssh/sshd_config"
            ],
            "common_causes": [
                "sshd service not running",
                "Firewall blocking port 22",
                "SSH listening on different port",
                "Host key issues",
                "Network/routing problems"
            ],
            "solutions": {
                "service_down": "sudo systemctl start sshd",
                "firewall": "sudo ufw allow ssh",
                "config_issue": "Check /etc/ssh/sshd_config, run sshd -t"
            }
        }
    },
    {
        "instruction": "Process is in D (uninterruptible sleep) state and won't die",
        "error_type": "process_stuck",
        "response": {
            "status": "difficult_recovery",
            "explanation": "D state means process is waiting on I/O and can't be interrupted, even by SIGKILL",
            "common_causes": [
                "Waiting on unresponsive NFS mount",
                "Disk I/O issues (failing drive)",
                "Kernel bug or driver issue",
                "USB device hanging"
            ],
            "diagnostic_steps": [
                "Check what it's waiting on: cat /proc/<pid>/stack",
                "Check for disk issues: dmesg | tail -50",
                "Check mounts: mount | grep nfs"
            ],
            "solutions": [
                "Wait for I/O to complete (may take time)",
                "Unmount hung NFS: umount -f /mount or umount -l /mount",
                "Fix underlying disk issue",
                "Last resort: reboot may be necessary"
            ]
        }
    },
    {
        "instruction": "I accidentally changed permissions on /etc or /var",
        "error_type": "permissions_disaster",
        "response": {
            "status": "serious",
            "severity": "high",
            "immediate_actions": [
                "DON'T REBOOT if system is still running",
                "DON'T LOG OUT - you may not be able to log back in"
            ],
            "recovery_options": [
                "If you know original perms, restore them",
                "Boot from live USB and fix permissions",
                "Reinstall packages: apt --reinstall install <package>",
                "Reset /etc to defaults from another system",
                "For /var, different subdirs need different perms"
            ],
            "common_fixes": {
                "/etc/shadow": "chmod 640, chown root:shadow",
                "/etc/passwd": "chmod 644, chown root:root",
                "/etc/sudoers": "chmod 440, chown root:root"
            },
            "prevention": "Never run recursive chmod/chown on system directories without double-checking"
        }
    },
    {
        "instruction": "Kernel panic - not syncing",
        "error_type": "system_crash",
        "response": {
            "status": "needs_investigation",
            "explanation": "Kernel panic means the kernel encountered an unrecoverable error",
            "common_causes": [
                "Hardware failure (RAM, disk)",
                "Corrupted filesystem",
                "Bad kernel module or driver",
                "Kernel bug or incompatibility"
            ],
            "recovery_steps": [
                "Boot to previous kernel (hold Shift at boot for GRUB menu)",
                "Boot to recovery mode",
                "From live USB: fsck filesystem, check logs",
                "Review /var/log/kern.log for clues"
            ],
            "hardware_tests": [
                "Test RAM: memtest86+",
                "Test disk: smartctl -a /dev/sda",
                "Check temperatures"
            ]
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
        "shell": "bash",
        "command": command,
        "explanation": explanation,
        "requires_sudo": "sudo" in command
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
    """Generate tool selection training examples.
    
    Samples from each category to keep total around 150 examples,
    balanced with other domains like Windows (~138).
    """
    examples = []
    
    # Sample from each category to balance the dataset
    # Total ~150 examples instead of ~329
    SAMPLES_PER_CATEGORY = {
        'basic': 25,      # from 61
        'advanced': 35,   # from 92
        'systemd': 25,    # from 53
        'networking': 35, # from 67
        'package': 25,    # from 56
    }
    
    random.seed(42)  # Reproducible sampling
    
    categories = [
        (BASIC_BASH_TASKS, SAMPLES_PER_CATEGORY['basic']),
        (ADVANCED_BASH_TASKS, SAMPLES_PER_CATEGORY['advanced']),
        (SYSTEMD_TASKS, SAMPLES_PER_CATEGORY['systemd']),
        (NETWORKING_TASKS, SAMPLES_PER_CATEGORY['networking']),
        (PACKAGE_MANAGEMENT_TASKS, SAMPLES_PER_CATEGORY['package']),
    ]
    
    for task_list, sample_size in categories:
        sampled = random.sample(task_list, min(sample_size, len(task_list)))
        for task in sampled:
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
    
    for concept in BASIC_CONCEPTS + ADVANCED_CONCEPTS:
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
    
    # Common admin queries
    admin_variations = [
        ("How do I check which Linux distro I'm running?", "Several ways: cat /etc/os-release (detailed info), lsb_release -a (if available), uname -a (kernel info), hostnamectl (systemd systems). The /etc/os-release file is most reliable across distros."),
        ("What's eating all my memory?", "Check with: free -h (overall), ps aux --sort=-%mem | head (top memory users), top then press M to sort by memory. Note: Linux caches aggressively - 'available' memory is what matters, not 'free'. Use smem for detailed per-process memory."),
        ("How do I find which package provides a command?", "Debian/Ubuntu: apt-file search /usr/bin/command or dpkg -S $(which command). Red Hat: yum provides */command or rpm -qf $(which command). Install apt-file first: apt install apt-file && apt-file update."),
        ("How do I run a command in the background?", "Append & to run in background: command &. Use nohup to survive logout: nohup command &. Use screen or tmux for persistent sessions. Jobs in background can be managed with jobs, fg, bg commands."),
        ("How do I check open files by a process?", "Use lsof -p <pid> for all open files, or lsof -c processname. For a specific file: lsof /path/to/file shows which processes have it open. fuser /path/to/file also works."),
    ]
    
    for query, answer in admin_variations:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    # Shell tips
    shell_tips = [
        ("What's the difference between > and >> in bash?", "> redirects output, overwriting the file. >> appends to the file. Use 2> for stderr, &> for both stdout and stderr. Example: command > file.log 2>&1 redirects both to file."),
        ("How do I use variables in bash?", "Assign without spaces: VAR=value. Use with $VAR or ${VAR}. Export for child processes: export VAR. Special vars: $?, $!, $$, $@, $#. Arrays: arr=(a b c); echo ${arr[0]}. Quote variables to handle spaces: \"$VAR\"."),
        ("What does set -e do in bash scripts?", "set -e exits the script if any command fails (returns non-zero). Combined with set -u (error on undefined variables) and set -o pipefail (catch pipe failures). Common script header: set -euo pipefail. Use || true to allow specific failures."),
    ]
    
    for query, answer in shell_tips:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    return variations

def main():
    """Generate all Linux training data."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Linux System Administration Training Data")
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
    output_file = output_dir / "linux_admin.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Linux Training Data Generation Complete!")
    print("=" * 60)
    print(f"Total examples: {len(all_examples)}")
    print(f"  Tool selection: {len(tool_examples)}")
    print(f"  Planning: {len(planning_examples)}")
    print(f"  Concepts: {len(concept_examples)}")
    print(f"  Error handling: {len(error_examples)}")
    print(f"  Variations: {len(variations)}")

if __name__ == "__main__":
    main()
