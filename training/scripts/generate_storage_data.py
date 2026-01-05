#!/usr/bin/env python3
"""
Storage & RAID Training Data Generator
Generates training examples for storage management, RAID, disk operations, and file systems.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, an AI assistant for developers. You help with storage management, RAID configuration, disk operations, file systems, backup strategies, and performance optimization. Respond in JSON format for actionable requests or plain text for conceptual questions."""

# ============================================================================
# STORAGE COMMAND TASKS
# ============================================================================

LINUX_STORAGE_TASKS = {
    "check disk space on all mounted volumes": {
        "tool": "terminal",
        "command": "df -h",
        "explanation": "Display disk space usage for all mounted filesystems in human-readable format"
    },
    "show detailed disk usage for current directory": {
        "tool": "terminal",
        "command": "du -sh ./*",
        "explanation": "Show size of each file and directory in current location"
    },
    "find largest files in the system": {
        "tool": "terminal",
        "command": "find / -type f -exec du -h {} + 2>/dev/null | sort -rh | head -20",
        "explanation": "Find the 20 largest files across the entire system"
    },
    "list all block devices": {
        "tool": "terminal",
        "command": "lsblk -f",
        "explanation": "List all block devices with filesystem information"
    },
    "check disk health with SMART": {
        "tool": "terminal",
        "command": "sudo smartctl -a /dev/sda",
        "explanation": "Display SMART health data for the specified disk"
    },
    "monitor disk I/O in real-time": {
        "tool": "terminal",
        "command": "sudo iotop -o",
        "explanation": "Show processes with active disk I/O"
    },
    "check filesystem integrity": {
        "tool": "terminal",
        "command": "sudo fsck -n /dev/sda1",
        "explanation": "Check filesystem without making changes (dry run)"
    },
    "show RAID array status": {
        "tool": "terminal",
        "command": "cat /proc/mdstat",
        "explanation": "Display status of all software RAID arrays"
    },
    "view detailed mdadm RAID info": {
        "tool": "terminal",
        "command": "sudo mdadm --detail /dev/md0",
        "explanation": "Show detailed information about a specific RAID array"
    },
    "list LVM physical volumes": {
        "tool": "terminal",
        "command": "sudo pvs",
        "explanation": "List all LVM physical volumes"
    },
    "show LVM volume groups": {
        "tool": "terminal",
        "command": "sudo vgs",
        "explanation": "Display all LVM volume groups"
    },
    "list logical volumes": {
        "tool": "terminal",
        "command": "sudo lvs",
        "explanation": "Show all LVM logical volumes"
    },
    "check NFS mounts": {
        "tool": "terminal",
        "command": "showmount -e localhost",
        "explanation": "List NFS exports from the server"
    },
    "view mounted filesystems": {
        "tool": "terminal",
        "command": "mount | grep -E '^/dev'",
        "explanation": "Show all mounted block devices"
    },
    "check inode usage": {
        "tool": "terminal",
        "command": "df -i",
        "explanation": "Display inode usage for all filesystems"
    }
}

WINDOWS_STORAGE_TASKS = {
    "check disk space on all drives": {
        "tool": "terminal",
        "command": "Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free, @{N='Size';E={$_.Used+$_.Free}}",
        "explanation": "Display disk space for all mounted drives"
    },
    "show disk partitions": {
        "tool": "terminal",
        "command": "Get-Partition | Select-Object DiskNumber, PartitionNumber, DriveLetter, Size, Type",
        "explanation": "List all disk partitions with details"
    },
    "list physical disks": {
        "tool": "terminal",
        "command": "Get-PhysicalDisk | Select-Object DeviceId, MediaType, Size, HealthStatus, OperationalStatus",
        "explanation": "Display all physical disks with health status"
    },
    "check volume health": {
        "tool": "terminal",
        "command": "Get-Volume | Select-Object DriveLetter, FileSystemLabel, HealthStatus, SizeRemaining, Size",
        "explanation": "Show health status of all volumes"
    },
    "view Storage Spaces pools": {
        "tool": "terminal",
        "command": "Get-StoragePool | Select-Object FriendlyName, HealthStatus, OperationalStatus, Size, AllocatedSize",
        "explanation": "Display Storage Spaces pool information"
    },
    "check RAID status with diskpart": {
        "tool": "terminal",
        "command": "echo list volume | diskpart",
        "explanation": "List all volumes including RAID status via diskpart"
    },
    "find large files on C drive": {
        "tool": "terminal",
        "command": "Get-ChildItem -Path C:\\ -Recurse -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 20 FullName, @{N='SizeGB';E={[math]::Round($_.Length/1GB,2)}}",
        "explanation": "Find 20 largest files on C: drive"
    },
    "analyze folder sizes": {
        "tool": "terminal",
        "command": "Get-ChildItem -Path . -Directory | ForEach-Object { $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; [PSCustomObject]@{Name=$_.Name; SizeMB=[math]::Round($size/1MB,2)} } | Sort-Object SizeMB -Descending",
        "explanation": "Show sizes of subdirectories in current folder"
    },
    "check disk performance counters": {
        "tool": "terminal",
        "command": "Get-Counter '\\PhysicalDisk(*)\\% Disk Time', '\\PhysicalDisk(*)\\Disk Read Bytes/sec', '\\PhysicalDisk(*)\\Disk Write Bytes/sec' -SampleInterval 1 -MaxSamples 5",
        "explanation": "Monitor disk performance metrics"
    },
    "optimize drive (defrag/trim)": {
        "tool": "terminal",
        "command": "Optimize-Volume -DriveLetter C -Verbose",
        "explanation": "Defragment HDD or TRIM SSD on C: drive"
    }
}

# ============================================================================
# RAID CONFIGURATION TASKS
# ============================================================================

RAID_TASKS = {
    "create RAID 1 mirror array": {
        "tool": "terminal",
        "command": "sudo mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdb /dev/sdc",
        "explanation": "Create a RAID 1 mirror array with two disks"
    },
    "create RAID 5 array with three disks": {
        "tool": "terminal",
        "command": "sudo mdadm --create /dev/md0 --level=5 --raid-devices=3 /dev/sdb /dev/sdc /dev/sdd",
        "explanation": "Create a RAID 5 array with parity across three disks"
    },
    "create RAID 10 array": {
        "tool": "terminal",
        "command": "sudo mdadm --create /dev/md0 --level=10 --raid-devices=4 /dev/sdb /dev/sdc /dev/sdd /dev/sde",
        "explanation": "Create a RAID 10 (mirrored stripe) array with four disks"
    },
    "add spare disk to RAID array": {
        "tool": "terminal",
        "command": "sudo mdadm --add /dev/md0 /dev/sdf",
        "explanation": "Add a hot spare disk to existing RAID array"
    },
    "remove failed disk from RAID": {
        "tool": "terminal",
        "command": "sudo mdadm --remove /dev/md0 /dev/sdc",
        "explanation": "Remove a failed disk from the RAID array"
    },
    "mark disk as failed for replacement": {
        "tool": "terminal",
        "command": "sudo mdadm --fail /dev/md0 /dev/sdc",
        "explanation": "Mark a disk as failed to trigger rebuild with spare"
    },
    "grow RAID array with new disk": {
        "tool": "terminal",
        "command": "sudo mdadm --grow /dev/md0 --raid-devices=4 --add /dev/sdf",
        "explanation": "Expand RAID array by adding a new disk"
    },
    "save RAID configuration": {
        "tool": "terminal",
        "command": "sudo mdadm --detail --scan >> /etc/mdadm/mdadm.conf",
        "explanation": "Save RAID configuration for persistence across reboots"
    },
    "stop RAID array": {
        "tool": "terminal",
        "command": "sudo mdadm --stop /dev/md0",
        "explanation": "Stop and deactivate a RAID array"
    },
    "assemble RAID array manually": {
        "tool": "terminal",
        "command": "sudo mdadm --assemble /dev/md0 /dev/sdb /dev/sdc",
        "explanation": "Manually assemble RAID array from component disks"
    }
}

# ============================================================================
# LVM TASKS
# ============================================================================

LVM_TASKS = {
    "create physical volume": {
        "tool": "terminal",
        "command": "sudo pvcreate /dev/sdb",
        "explanation": "Initialize a disk as an LVM physical volume"
    },
    "create volume group": {
        "tool": "terminal",
        "command": "sudo vgcreate vg_data /dev/sdb /dev/sdc",
        "explanation": "Create a volume group from physical volumes"
    },
    "create logical volume": {
        "tool": "terminal",
        "command": "sudo lvcreate -L 100G -n lv_storage vg_data",
        "explanation": "Create a 100GB logical volume named lv_storage"
    },
    "extend logical volume": {
        "tool": "terminal",
        "command": "sudo lvextend -L +50G /dev/vg_data/lv_storage",
        "explanation": "Add 50GB to an existing logical volume"
    },
    "resize filesystem after LVM extend": {
        "tool": "terminal",
        "command": "sudo resize2fs /dev/vg_data/lv_storage",
        "explanation": "Resize ext4 filesystem to use expanded LVM space"
    },
    "create LVM snapshot": {
        "tool": "terminal",
        "command": "sudo lvcreate -L 10G -s -n lv_storage_snap /dev/vg_data/lv_storage",
        "explanation": "Create a 10GB snapshot of a logical volume"
    },
    "extend volume group with new disk": {
        "tool": "terminal",
        "command": "sudo vgextend vg_data /dev/sdd",
        "explanation": "Add a new physical volume to an existing volume group"
    },
    "display LVM snapshot status": {
        "tool": "terminal",
        "command": "sudo lvs -o +snap_percent",
        "explanation": "Show logical volumes with snapshot usage percentage"
    },
    "remove logical volume": {
        "tool": "terminal",
        "command": "sudo lvremove /dev/vg_data/lv_storage",
        "explanation": "Delete a logical volume"
    },
    "thin provisioned LVM pool": {
        "tool": "terminal",
        "command": "sudo lvcreate -L 500G -T vg_data/thin_pool",
        "explanation": "Create a thin provisioned storage pool"
    }
}

# ============================================================================
# BACKUP & RECOVERY TASKS
# ============================================================================

BACKUP_TASKS = {
    "create compressed tar backup": {
        "tool": "terminal",
        "command": "tar -czvf backup_$(date +%Y%m%d).tar.gz /path/to/data",
        "explanation": "Create a gzip compressed tar archive with date stamp"
    },
    "incremental backup with rsync": {
        "tool": "terminal",
        "command": "rsync -avz --delete --backup --backup-dir=incremental_$(date +%Y%m%d) /source/ /backup/",
        "explanation": "Sync files with incremental backup of changed files"
    },
    "create disk image with dd": {
        "tool": "terminal",
        "command": "sudo dd if=/dev/sda of=/backup/disk_image.img bs=4M status=progress",
        "explanation": "Create a complete disk image for disaster recovery"
    },
    "verify backup integrity": {
        "tool": "terminal",
        "command": "tar -tvzf backup.tar.gz > /dev/null && echo 'Backup verified'",
        "explanation": "Test tar archive integrity without extracting"
    },
    "setup restic backup repository": {
        "tool": "terminal",
        "command": "restic init --repo /backup/restic-repo",
        "explanation": "Initialize a new restic backup repository"
    },
    "create restic backup": {
        "tool": "terminal",
        "command": "restic -r /backup/restic-repo backup /data --verbose",
        "explanation": "Create deduplicated encrypted backup with restic"
    },
    "restore from restic snapshot": {
        "tool": "terminal",
        "command": "restic -r /backup/restic-repo restore latest --target /restore",
        "explanation": "Restore the latest snapshot to target directory"
    },
    "Windows backup with robocopy": {
        "tool": "terminal",
        "command": "robocopy C:\\Data D:\\Backup /MIR /Z /MT:8 /LOG:backup.log",
        "explanation": "Mirror backup with multi-threading and logging"
    },
    "schedule Windows backup task": {
        "tool": "terminal",
        "command": "schtasks /Create /SC DAILY /TN \"DailyBackup\" /TR \"robocopy C:\\Data D:\\Backup /MIR\" /ST 02:00",
        "explanation": "Create scheduled task for daily backup at 2 AM"
    },
    "create ZFS snapshot": {
        "tool": "terminal",
        "command": "sudo zfs snapshot tank/data@$(date +%Y%m%d)",
        "explanation": "Create a ZFS snapshot with date stamp"
    }
}

# ============================================================================
# FILESYSTEM TASKS
# ============================================================================

FILESYSTEM_TASKS = {
    "format partition as ext4": {
        "tool": "terminal",
        "command": "sudo mkfs.ext4 -L data /dev/sdb1",
        "explanation": "Create ext4 filesystem with label 'data'"
    },
    "format partition as XFS": {
        "tool": "terminal",
        "command": "sudo mkfs.xfs -L storage /dev/sdb1",
        "explanation": "Create XFS filesystem with label"
    },
    "create Btrfs filesystem": {
        "tool": "terminal",
        "command": "sudo mkfs.btrfs -L btrfs_data /dev/sdb1",
        "explanation": "Create Btrfs filesystem with label"
    },
    "mount filesystem": {
        "tool": "terminal",
        "command": "sudo mount /dev/sdb1 /mnt/data",
        "explanation": "Mount a partition to a directory"
    },
    "add entry to fstab for permanent mount": {
        "tool": "terminal",
        "command": "echo 'UUID=$(blkid -s UUID -o value /dev/sdb1) /mnt/data ext4 defaults 0 2' | sudo tee -a /etc/fstab",
        "explanation": "Add filesystem to fstab for automatic mounting"
    },
    "check and repair ext4 filesystem": {
        "tool": "terminal",
        "command": "sudo e2fsck -p /dev/sdb1",
        "explanation": "Automatically repair ext4 filesystem errors"
    },
    "resize ext4 filesystem": {
        "tool": "terminal",
        "command": "sudo resize2fs /dev/sdb1",
        "explanation": "Expand ext4 filesystem to fill partition"
    },
    "create Btrfs subvolume": {
        "tool": "terminal",
        "command": "sudo btrfs subvolume create /mnt/btrfs/@home",
        "explanation": "Create a Btrfs subvolume for /home"
    },
    "create ZFS pool": {
        "tool": "terminal",
        "command": "sudo zpool create tank mirror /dev/sdb /dev/sdc",
        "explanation": "Create a mirrored ZFS pool"
    },
    "enable ZFS compression": {
        "tool": "terminal",
        "command": "sudo zfs set compression=lz4 tank/data",
        "explanation": "Enable LZ4 compression on ZFS dataset"
    }
}

# ============================================================================
# PLANNING TASKS
# ============================================================================

PLANNING_TASKS = [
    {
        "instruction": "I need to set up a RAID 5 array with 4 disks and LVM on top for flexible storage management",
        "response": {
            "action": "multi_step_plan",
            "plan": [
                {"step": 1, "action": "Verify disks are available and unpartitioned", "command": "lsblk -f", "checkpoint": "All 4 disks show as empty"},
                {"step": 2, "action": "Create RAID 5 array", "command": "sudo mdadm --create /dev/md0 --level=5 --raid-devices=4 /dev/sd{b,c,d,e}", "checkpoint": "RAID array created"},
                {"step": 3, "action": "Wait for initial sync", "command": "watch cat /proc/mdstat", "checkpoint": "Sync reaches 100%"},
                {"step": 4, "action": "Save RAID configuration", "command": "sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf", "checkpoint": "Config saved"},
                {"step": 5, "action": "Create physical volume on RAID", "command": "sudo pvcreate /dev/md0", "checkpoint": "PV created"},
                {"step": 6, "action": "Create volume group", "command": "sudo vgcreate vg_raid /dev/md0", "checkpoint": "VG created"},
                {"step": 7, "action": "Create logical volume", "command": "sudo lvcreate -l 100%FREE -n lv_data vg_raid", "checkpoint": "LV spans full VG"},
                {"step": 8, "action": "Format with ext4", "command": "sudo mkfs.ext4 /dev/vg_raid/lv_data", "checkpoint": "Filesystem created"},
                {"step": 9, "action": "Mount and add to fstab", "command": "sudo mkdir -p /data && sudo mount /dev/vg_raid/lv_data /data", "checkpoint": "Mounted successfully"},
                {"step": 10, "action": "Update initramfs for boot", "command": "sudo update-initramfs -u", "checkpoint": "Initramfs updated"}
            ],
            "notes": "RAID 5 provides ~75% usable capacity with single-disk fault tolerance. LVM allows easy resizing."
        }
    },
    {
        "instruction": "Help me set up a comprehensive backup strategy for a production database server",
        "response": {
            "action": "multi_step_plan",
            "plan": [
                {"step": 1, "action": "Install restic backup tool", "command": "sudo apt install restic -y", "checkpoint": "Restic installed"},
                {"step": 2, "action": "Create local backup repository", "command": "restic init --repo /backup/local", "checkpoint": "Local repo initialized"},
                {"step": 3, "action": "Configure remote S3 backup", "command": "export AWS_ACCESS_KEY_ID=xxx; restic init --repo s3:s3.amazonaws.com/bucket/backup", "checkpoint": "S3 repo ready"},
                {"step": 4, "action": "Create backup script", "command": "Create /opt/backup/backup.sh with pre/post hooks for DB dump", "checkpoint": "Script created"},
                {"step": 5, "action": "Add database dump hook", "command": "pg_dump dbname > /tmp/db_dump.sql as pre-backup step", "checkpoint": "DB dump integrated"},
                {"step": 6, "action": "Configure backup retention", "command": "restic forget --keep-hourly 24 --keep-daily 7 --keep-weekly 4 --keep-monthly 12", "checkpoint": "Retention policy set"},
                {"step": 7, "action": "Schedule hourly backups", "command": "crontab: 0 * * * * /opt/backup/backup.sh >> /var/log/backup.log 2>&1", "checkpoint": "Cron job added"},
                {"step": 8, "action": "Set up backup monitoring", "command": "Add check for backup age and alert if > 2 hours old", "checkpoint": "Monitoring active"},
                {"step": 9, "action": "Test restore procedure", "command": "restic restore latest --target /tmp/restore-test", "checkpoint": "Restore verified"},
                {"step": 10, "action": "Document recovery runbook", "command": "Create step-by-step recovery documentation", "checkpoint": "Runbook complete"}
            ],
            "notes": "3-2-1 backup rule: 3 copies, 2 different media types, 1 offsite. Test restores regularly!"
        }
    },
    {
        "instruction": "I need to migrate data from old storage array to new ZFS pool with minimal downtime",
        "response": {
            "action": "multi_step_plan",
            "plan": [
                {"step": 1, "action": "Verify new disks and health", "command": "sudo smartctl -t long /dev/sd{b,c,d,e}; sleep 2h; sudo smartctl -a /dev/sdb", "checkpoint": "All disks healthy"},
                {"step": 2, "action": "Create ZFS mirror pool", "command": "sudo zpool create -o ashift=12 tank mirror /dev/sdb /dev/sdc mirror /dev/sdd /dev/sde", "checkpoint": "Pool created with 2 mirrors"},
                {"step": 3, "action": "Enable compression and dedup", "command": "sudo zfs set compression=lz4 tank; sudo zfs set dedup=on tank", "checkpoint": "Features enabled"},
                {"step": 4, "action": "Create datasets with quotas", "command": "sudo zfs create -o quota=500G tank/data", "checkpoint": "Dataset ready"},
                {"step": 5, "action": "Initial data sync with rsync", "command": "sudo rsync -avz --progress /old_storage/ /tank/data/", "checkpoint": "Initial sync complete"},
                {"step": 6, "action": "Schedule maintenance window", "command": "Notify users of 30-minute downtime", "checkpoint": "Users notified"},
                {"step": 7, "action": "Stop applications", "command": "sudo systemctl stop app.service", "checkpoint": "Services stopped"},
                {"step": 8, "action": "Final incremental sync", "command": "sudo rsync -avz --delete /old_storage/ /tank/data/", "checkpoint": "Final sync done"},
                {"step": 9, "action": "Update mount points", "command": "Update /etc/fstab and symlinks to point to new storage", "checkpoint": "Mounts updated"},
                {"step": 10, "action": "Start applications and verify", "command": "sudo systemctl start app.service; verify application functionality", "checkpoint": "Services running"},
                {"step": 11, "action": "Monitor ZFS pool health", "command": "zpool status tank; zpool iostat tank 5", "checkpoint": "Pool healthy"},
                {"step": 12, "action": "Decommission old storage after validation", "command": "After 1 week of operation, wipe old disks", "checkpoint": "Migration complete"}
            ],
            "notes": "ZFS provides checksumming, snapshots, and easy expansion. Always run SMART tests on new disks!"
        }
    },
    {
        "instruction": "Set up Storage Spaces Direct on Windows Server for highly available storage",
        "response": {
            "action": "multi_step_plan",
            "plan": [
                {"step": 1, "action": "Verify cluster nodes meet requirements", "command": "Test-Cluster -Node node1,node2,node3,node4", "checkpoint": "Cluster validation passes"},
                {"step": 2, "action": "Enable Storage Spaces Direct feature", "command": "Install-WindowsFeature -Name Failover-Clustering, FS-Data-Deduplication, Storage-Replica -IncludeManagementTools", "checkpoint": "Features installed"},
                {"step": 3, "action": "Create failover cluster", "command": "New-Cluster -Name S2DCluster -Node node1,node2,node3,node4 -NoStorage", "checkpoint": "Cluster created"},
                {"step": 4, "action": "Enable S2D on cluster", "command": "Enable-ClusterS2D -CacheState Disabled", "checkpoint": "S2D enabled"},
                {"step": 5, "action": "Create storage tier", "command": "New-StorageTier -StoragePoolFriendlyName S2D* -FriendlyName Performance -MediaType SSD", "checkpoint": "Tier created"},
                {"step": 6, "action": "Create virtual disk", "command": "New-Volume -StoragePoolFriendlyName S2D* -FriendlyName Volume1 -Size 1TB -ResiliencySettingName Mirror", "checkpoint": "Volume created"},
                {"step": 7, "action": "Configure CSV", "command": "Add-ClusterSharedVolume -Name 'Cluster Virtual Disk (Volume1)'", "checkpoint": "CSV configured"},
                {"step": 8, "action": "Set up monitoring", "command": "Configure Windows Admin Center for S2D monitoring", "checkpoint": "Monitoring active"}
            ],
            "notes": "S2D requires minimum 2 nodes (2-way mirror) or 3 nodes (3-way mirror) for production."
        }
    }
]

# ============================================================================
# CONCEPT Q&A
# ============================================================================

CONCEPT_QA = [
    # RAID Concepts
    {
        "instruction": "What is RAID and what are the different RAID levels?",
        "response": """RAID (Redundant Array of Independent Disks) combines multiple disks for performance, redundancy, or both.

**Common RAID Levels:**

| Level | Min Disks | Description | Use Case |
|-------|-----------|-------------|----------|
| **RAID 0** | 2 | Striping, no redundancy | Speed, scratch space |
| **RAID 1** | 2 | Mirroring, 50% capacity | OS drives, critical data |
| **RAID 5** | 3 | Striping with parity | General file storage |
| **RAID 6** | 4 | Double parity | Large arrays, critical data |
| **RAID 10** | 4 | Stripe of mirrors | Databases, high I/O |

**Key Trade-offs:**
- RAID 0: Maximum speed, zero protection
- RAID 1: Simple, but 50% capacity loss
- RAID 5: Good balance, but slow rebuild
- RAID 6: Better protection, slower writes
- RAID 10: Best performance + protection, expensive

**Important:** RAID is NOT a backup! It protects against disk failure, not data corruption, ransomware, or user error."""
    },
    {
        "instruction": "What's the difference between hardware RAID and software RAID?",
        "response": """**Hardware RAID:**
- Dedicated controller card with its own processor
- Handles RAID calculations in hardware
- Usually has battery-backed cache for write performance
- OS sees single disk, unaware of RAID
- Vendor-specific, can't move array to different controller
- More expensive, better performance under heavy load

**Software RAID:**
- Uses CPU for RAID calculations
- Examples: Linux mdadm, Windows Storage Spaces, ZFS
- Array portable between systems (mdadm/ZFS)
- No extra hardware cost
- Modern CPUs handle it easily
- More flexible, easier to recover

**Recommendation:**
- Small/medium workloads: Software RAID (mdadm or ZFS)
- Enterprise with high I/O: Hardware RAID with BBU
- Modern servers: Consider ZFS for features + protection

**ZFS/Btrfs** add checksumming that hardware RAID can't provide, detecting silent data corruption."""
    },
    {
        "instruction": "Explain LVM and why I should use it",
        "response": """**LVM (Logical Volume Manager)** adds a flexible abstraction layer between physical disks and filesystems.

**Architecture:**
```
Physical Disks → Physical Volumes (PV) → Volume Groups (VG) → Logical Volumes (LV) → Filesystems
```

**Benefits:**
1. **Resize on the fly** - Extend or shrink volumes without unmounting (ext4/XFS)
2. **Span multiple disks** - Create volumes larger than any single disk
3. **Snapshots** - Point-in-time copies for backup/testing
4. **Thin provisioning** - Allocate more space than physically available
5. **Easy disk management** - Add/remove disks from pool dynamically

**Common Use Cases:**
- Root filesystem that may need to grow
- Database storage requiring expansion
- VM storage with snapshots
- Flexible server storage pools

**Example Workflow:**
```bash
pvcreate /dev/sdb /dev/sdc    # Initialize disks
vgcreate data_vg /dev/sdb /dev/sdc  # Create pool
lvcreate -L 100G -n app_lv data_vg  # Create volume
mkfs.ext4 /dev/data_vg/app_lv  # Format
# Later: lvextend -L +50G /dev/data_vg/app_lv; resize2fs /dev/data_vg/app_lv
```

**Pro tip:** Combine LVM with RAID for flexibility AND redundancy."""
    },
    {
        "instruction": "What is ZFS and why do people love it?",
        "response": """**ZFS** is an advanced filesystem + volume manager combining features that usually require multiple tools.

**Why ZFS is Special:**

1. **End-to-end Checksumming** - Detects and corrects silent data corruption (bit rot)
2. **Copy-on-Write** - Never overwrites data, always writes to new location
3. **Instant Snapshots** - Create/delete snapshots in milliseconds
4. **Built-in RAID** - RAIDZ1/2/3 integrated with the filesystem
5. **Compression** - Transparent LZ4 compression (often faster than uncompressed!)
6. **Deduplication** - Optional block-level dedup
7. **Send/Receive** - Efficient incremental replication

**ZFS Concepts:**
- **Pool (zpool)** - Collection of disks
- **Dataset** - Like a filesystem within the pool
- **RAIDZ** - ZFS version of RAID5/6 (RAIDZ1, RAIDZ2, RAIDZ3)
- **Scrub** - Verify and repair data integrity

**Example Setup:**
```bash
zpool create tank mirror /dev/sdb /dev/sdc  # Mirrored pool
zfs set compression=lz4 tank                 # Enable compression
zfs create tank/data                         # Create dataset
zfs snapshot tank/data@backup                # Instant snapshot
```

**Considerations:**
- Memory hungry (1GB RAM per 1TB of storage recommended)
- License issues on Linux (built-in on FreeBSD)
- Can't shrink pools (but can add disks)

**Best for:** NAS, file servers, backup targets, data you care about."""
    },
    {
        "instruction": "How should I choose between ext4, XFS, Btrfs, and ZFS?",
        "response": """**Filesystem Comparison:**

| Feature | ext4 | XFS | Btrfs | ZFS |
|---------|------|-----|-------|-----|
| **Maturity** | Very stable | Very stable | Stable | Very stable |
| **Max size** | 1 EB | 8 EB | 16 EB | 256 ZB |
| **Snapshots** | No | No | Yes | Yes |
| **Checksums** | Metadata only | No | Yes | Yes |
| **Compression** | No | No | Yes | Yes |
| **RAID** | External | External | Built-in | Built-in |
| **Repair** | e2fsck | xfs_repair | btrfs check | Self-healing |

**When to Use Each:**

**ext4:**
- General purpose Linux filesystem
- Boot partitions, simple storage
- Maximum compatibility
- Best recovery tools

**XFS:**
- Large files (video, VMs)
- High-performance workloads
- RHEL default filesystem
- Great parallel I/O

**Btrfs:**
- Desktop Linux snapshots
- Fedora/SUSE default
- Subvolumes for organization
- Good for SSDs with compression

**ZFS:**
- Data integrity is critical
- NAS/file servers
- Need snapshots + replication
- Have RAM to spare

**Simple Rule:**
- Don't care? Use ext4
- Big files? Use XFS
- Want snapshots on Linux? Use Btrfs
- Data must never corrupt? Use ZFS"""
    },
    {
        "instruction": "What is thin provisioning and when should I use it?",
        "response": """**Thin Provisioning** allocates storage on-demand rather than reserving it all upfront.

**How It Works:**
- You create a 1TB volume
- Only actually consumed space is used (e.g., 100GB)
- As data is written, storage is allocated from pool

**Example:**
```
Thin Pool: 500GB physical
├── VM1: 200GB thin volume (using 50GB actual)
├── VM2: 200GB thin volume (using 75GB actual)
└── VM3: 200GB thin volume (using 100GB actual)
Total allocated: 600GB (but only 225GB physical used!)
```

**Benefits:**
- More efficient storage utilization
- Faster provisioning (no zeroing)
- Easier capacity planning
- Pay for storage as you need it

**Risks:**
- **Over-commitment** - If you allocate more than you have
- **Sudden fullness** - Pool can fill unexpectedly
- **Performance impact** - Allocation overhead

**Best Practices:**
1. Monitor pool capacity closely (alert at 70%)
2. Set reasonable overcommit ratios (1.5x max)
3. Use in virtualization, not critical databases
4. Have expansion plan ready

**Tools Supporting Thin Provisioning:**
- LVM thin pools
- VMware VMDK thin disks
- ZFS (inherently thin)
- Storage array features

**Use thin provisioning for:** VMs, dev environments, dynamic workloads
**Avoid for:** Databases, predictable high-capacity workloads"""
    },
    {
        "instruction": "Explain the 3-2-1 backup rule",
        "response": """**The 3-2-1 Backup Rule** is the gold standard for data protection:

**3** - Keep at least 3 copies of your data
**2** - Store backups on 2 different media types
**1** - Keep 1 copy offsite (or in the cloud)

**Why Each Matters:**

**3 Copies:**
- Original + 2 backups
- Protects against single backup failure
- Allows for verification against multiple sources

**2 Media Types:**
- Example: SSD + tape, or disk + cloud
- Different failure modes
- Media can fail simultaneously if same type/batch

**1 Offsite:**
- Protects against site disasters (fire, flood, theft)
- Ransomware can't reach air-gapped backups
- Cloud storage counts as offsite

**Modern Interpretation (3-2-1-1-0):**
- **3-2-1** plus
- **1** copy offline (air-gapped)
- **0** errors (verify backups work!)

**Example Implementation:**
```
Primary: Production server (copy 1)
Local:   NAS with nightly backup (copy 2, different media)
Cloud:   S3/Backblaze encrypted backup (copy 3, offsite)
Monthly: External HDD stored offsite (offline)
```

**Critical:** TEST YOUR RESTORES! A backup you haven't tested is not a backup."""
    },
    {
        "instruction": "What causes disk failures and how can I predict them?",
        "response": """**Common Causes of Disk Failure:**

**Mechanical (HDD):**
- Head crashes from shock/vibration
- Motor bearing wear
- Platter degradation
- Electronics failure

**Electronic (SSD/HDD):**
- Controller failure
- Power surges
- Capacitor aging
- Firmware bugs

**SSD-Specific:**
- Write endurance exhaustion (NAND wear)
- Sudden power loss without capacitor
- Cell degradation

**Prediction with SMART:**

SMART (Self-Monitoring, Analysis and Reporting Technology) provides early warning:

```bash
# Check SMART health
sudo smartctl -H /dev/sda

# Full SMART data
sudo smartctl -a /dev/sda

# Run long test
sudo smartctl -t long /dev/sda
```

**Critical SMART Attributes to Monitor:**

| Attribute | Warning Sign |
|-----------|--------------|
| Reallocated_Sector_Ct | Any increase is bad |
| Current_Pending_Sector | Sectors waiting reallocation |
| Offline_Uncorrectable | Unrecoverable read errors |
| UDMA_CRC_Error_Count | Cable/connection issues |
| Temperature | >50°C sustained |
| Power_On_Hours | >30,000 hours |
| Wear_Leveling_Count (SSD) | <20% remaining |

**Best Practices:**
1. Monitor SMART weekly (smartd daemon)
2. Replace drives showing any reallocated sectors
3. Keep drives cool (<45°C ideal)
4. Replace drives proactively at 5-7 years
5. Buy drives from different batches to avoid batch failures

**Tools:** smartmontools, CrystalDiskInfo (Windows), hdsentinel"""
    }
]

# ============================================================================
# ERROR & TROUBLESHOOTING SCENARIOS
# ============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "My RAID array shows one disk as failed, what do I do?",
        "response": {
            "status": "error_recovery",
            "error": "RAID disk failure",
            "immediate_actions": [
                "Check if array is still operational: cat /proc/mdstat",
                "Identify the failed disk: sudo mdadm --detail /dev/md0",
                "Check if hot spare is available and rebuilding"
            ],
            "recovery_steps": [
                {"step": 1, "action": "Verify array status", "command": "cat /proc/mdstat", "note": "Should show degraded state"},
                {"step": 2, "action": "Get failed disk serial", "command": "sudo smartctl -a /dev/sdX | grep Serial"},
                {"step": 3, "action": "Remove failed disk from array", "command": "sudo mdadm --remove /dev/md0 /dev/sdX"},
                {"step": 4, "action": "Physically replace disk"},
                {"step": 5, "action": "Partition new disk identically", "command": "sudo sfdisk -d /dev/sda | sudo sfdisk /dev/sdX"},
                {"step": 6, "action": "Add new disk to array", "command": "sudo mdadm --add /dev/md0 /dev/sdX1"},
                {"step": 7, "action": "Monitor rebuild", "command": "watch cat /proc/mdstat"}
            ],
            "warning": "DO NOT power off during rebuild! Ensure good backups exist before ANY RAID maintenance."
        }
    },
    {
        "instruction": "I'm getting 'No space left on device' but df shows space available",
        "response": {
            "status": "troubleshooting",
            "error": "No space left on device with available space",
            "possible_causes": [
                "Inode exhaustion (many small files)",
                "Reserved blocks for root user",
                "Deleted files held open by processes",
                "Quota limits reached"
            ],
            "diagnostic_commands": [
                {"check": "Inode usage", "command": "df -i", "look_for": "100% IUse%"},
                {"check": "Open deleted files", "command": "sudo lsof +L1", "look_for": "Large deleted files"},
                {"check": "Reserved blocks", "command": "sudo tune2fs -l /dev/sda1 | grep -i reserved"},
                {"check": "User quotas", "command": "quota -u $USER"}
            ],
            "solutions": {
                "inode_exhaustion": "Find and delete small files: find /path -type f | wc -l; find /path -type f -empty -delete",
                "deleted_files": "Restart processes holding deleted files or: > /proc/PID/fd/FD_NUMBER",
                "reserved_blocks": "Reduce reserved blocks: sudo tune2fs -m 1 /dev/sda1",
                "quota": "Contact admin to increase quota"
            }
        }
    },
    {
        "instruction": "Disk I/O is extremely slow, how do I diagnose it?",
        "response": {
            "status": "troubleshooting",
            "error": "Slow disk I/O performance",
            "diagnostic_approach": [
                {"step": 1, "action": "Check I/O wait", "command": "vmstat 1 5", "look_for": "High wa% column"},
                {"step": 2, "action": "Identify I/O heavy processes", "command": "sudo iotop -oa", "look_for": "Processes with high DISK READ/WRITE"},
                {"step": 3, "action": "Check disk queue depth", "command": "iostat -x 1 5", "look_for": "await > 20ms, %util > 80%"},
                {"step": 4, "action": "Check for disk errors", "command": "dmesg | grep -i -E 'error|fail|bad|timeout'"},
                {"step": 5, "action": "Check SMART health", "command": "sudo smartctl -a /dev/sda | grep -E 'Reallocated|Pending|Uncorrectable'"},
                {"step": 6, "action": "Check filesystem health", "command": "sudo xfs_repair -n /dev/sda1 or sudo fsck -n /dev/sda1"}
            ],
            "common_causes": [
                "Failing disk (check SMART)",
                "Filesystem fragmentation",
                "Too many processes competing for I/O",
                "RAID rebuild in progress",
                "Swap thrashing (memory issue)",
                "Network storage (NFS/iSCSI) issues"
            ],
            "quick_fixes": {
                "process_killing_io": "Use ionice to reduce priority: ionice -c3 -p PID",
                "tune_scheduler": "For SSDs: echo noop > /sys/block/sda/queue/scheduler",
                "filesystem_check": "Schedule fsck on next reboot"
            }
        }
    },
    {
        "instruction": "My ZFS pool shows DEGRADED status",
        "response": {
            "status": "error_recovery",
            "error": "ZFS pool degraded",
            "severity": "High - Act quickly but don't panic",
            "immediate_check": "sudo zpool status",
            "recovery_procedure": [
                {"step": 1, "action": "Get detailed status", "command": "sudo zpool status -v"},
                {"step": 2, "action": "Identify failed device", "look_for": "UNAVAIL, FAULTED, or DEGRADED state"},
                {"step": 3, "action": "Check disk health", "command": "sudo smartctl -a /dev/failing_disk"},
                {"step": 4, "action": "If recoverable error, clear and scrub", "command": "sudo zpool clear tank; sudo zpool scrub tank"},
                {"step": 5, "action": "If disk failed, replace", "command": "sudo zpool replace tank /dev/old_disk /dev/new_disk"},
                {"step": 6, "action": "Monitor resilver progress", "command": "sudo zpool status tank"}
            ],
            "warnings": [
                "Do not lose another disk during resilver (CRITICAL data loss)",
                "Ensure good backups exist",
                "Consider adding spare disk after recovery",
                "Run scrub monthly to detect issues early"
            ]
        }
    },
    {
        "instruction": "LVM snapshot is filling up rapidly, what should I do?",
        "response": {
            "status": "urgent",
            "error": "LVM snapshot filling up",
            "problem": "Snapshots store only changes, but if source volume changes heavily, snapshot fills up and becomes invalid",
            "immediate_action": "Check snapshot status: sudo lvs -o +snap_percent",
            "options": [
                {
                    "option": "Extend snapshot",
                    "command": "sudo lvextend -L +10G /dev/vg/snapshot",
                    "note": "Buys time but not permanent solution"
                },
                {
                    "option": "Complete backup and remove snapshot",
                    "command": "Finish your backup task, then: sudo lvremove /dev/vg/snapshot",
                    "note": "Snapshots are for short-term use"
                },
                {
                    "option": "Use thin snapshots instead",
                    "command": "Thin snapshots share space more efficiently",
                    "note": "Requires thin pool setup"
                }
            ],
            "best_practices": [
                "Size snapshots for expected change rate",
                "Monitor snapshot usage continuously",
                "Complete snapshot-based operations quickly",
                "Consider ZFS/Btrfs for better snapshot handling"
            ]
        }
    },
    {
        "instruction": "NFS mount hanging or extremely slow",
        "response": {
            "status": "troubleshooting",
            "error": "NFS performance issues",
            "diagnostic_steps": [
                {"check": "Server reachable", "command": "ping nfs-server"},
                {"check": "NFS ports open", "command": "rpcinfo -p nfs-server"},
                {"check": "Current mount options", "command": "mount | grep nfs"},
                {"check": "NFS statistics", "command": "nfsstat -c"}
            ],
            "common_causes": [
                "Network congestion or firewall issues",
                "Server overloaded",
                "Hard mount timeout (default, blocks until server responds)",
                "Version mismatch (v3 vs v4)"
            ],
            "solutions": {
                "hanging_mount": "Use soft mount with timeout: mount -o soft,timeo=10 server:/share /mnt",
                "slow_performance": "Try async writes, larger rsize/wsize: mount -o async,rsize=32768,wsize=32768",
                "firewall": "Ensure ports 111, 2049 (and mountd for v3) are open",
                "force_nfs4": "mount -t nfs4 server:/share /mnt"
            }
        }
    },
    {
        "instruction": "Accidentally deleted files, how to recover?",
        "response": {
            "status": "urgent",
            "error": "Accidental file deletion",
            "critical_first_step": "STOP writing to the filesystem immediately! Every write reduces recovery chances.",
            "recovery_options": [
                {
                    "scenario": "ext4 filesystem",
                    "tool": "extundelete",
                    "command": "sudo extundelete /dev/sda1 --restore-all",
                    "note": "Unmount filesystem first if possible"
                },
                {
                    "scenario": "Any filesystem",
                    "tool": "photorec/testdisk",
                    "command": "sudo photorec /dev/sda1",
                    "note": "Recovers by file signature, loses filenames"
                },
                {
                    "scenario": "File still open by process",
                    "command": "Check /proc/PID/fd/ for open file descriptors",
                    "note": "cp /proc/PID/fd/FD recovered_file"
                }
            ],
            "prevention": [
                "Regular backups are ONLY reliable recovery",
                "Use trash-cli instead of rm",
                "Consider ZFS snapshots for instant recovery"
            ]
        }
    },
    {
        "instruction": "Btrfs filesystem showing read-only after error",
        "response": {
            "status": "error_recovery",
            "error": "Btrfs forced read-only mode",
            "explanation": "Btrfs remounts read-only when it detects corruption to prevent further damage",
            "recovery_procedure": [
                {"step": 1, "action": "Check dmesg for error details", "command": "dmesg | grep -i btrfs | tail -50"},
                {"step": 2, "action": "Attempt scrub to find corruption", "command": "sudo btrfs scrub start /mnt"},
                {"step": 3, "action": "Check balance status", "command": "sudo btrfs balance status /mnt"},
                {"step": 4, "action": "Try recovery mount", "command": "sudo mount -o recovery,ro /dev/sda1 /mnt"},
                {"step": 5, "action": "If needed, repair", "command": "sudo btrfs check --repair /dev/sda1", "warning": "Last resort only!"}
            ],
            "common_causes": [
                "Disk hardware failure",
                "Unexpected power loss",
                "Kernel bugs (keep kernel updated)",
                "RAID array issues"
            ],
            "note": "BACKUP DATA BEFORE repair attempts. Btrfs repair can make things worse."
        }
    },
    {
        "instruction": "Windows disk showing as 'Not Initialized' after connecting",
        "response": {
            "status": "troubleshooting",
            "error": "Disk not initialized in Windows",
            "warning": "Initializing will ERASE all data - check if disk has existing data first",
            "diagnosis": [
                "Check Disk Management: diskmgmt.msc",
                "Try diskpart: list disk (check if seen)",
                "Check if from another OS (GPT/MBR mismatch)"
            ],
            "if_new_disk": {
                "steps": [
                    "Open Disk Management",
                    "Right-click disk → Initialize Disk",
                    "Choose GPT for >2TB or modern systems",
                    "Create new simple volume"
                ]
            },
            "if_has_data": {
                "do_not": "Do NOT initialize - will erase all data!",
                "try": [
                    "Use testdisk to recover partition table",
                    "If Linux formatted: use ext2fsd or WSL to read",
                    "If encryption: need original encryption keys"
                ]
            }
        }
    },
    {
        "instruction": "SSD TRIM not working, how to verify and enable?",
        "response": {
            "status": "optimization",
            "error": "TRIM may not be active",
            "why_trim_matters": "TRIM tells SSD which blocks are free, maintains performance over time",
            "verification": {
                "linux": [
                    "Check filesystem supports TRIM: sudo fstrim -v /",
                    "Check discard mount option: mount | grep discard",
                    "Verify SSD supports TRIM: sudo hdparm -I /dev/sda | grep TRIM"
                ],
                "windows": "fsutil behavior query DisableDeleteNotify (0 = enabled)"
            },
            "enable_linux": {
                "periodic_trim": "sudo systemctl enable fstrim.timer",
                "continuous_trim": "Add 'discard' to fstab mount options",
                "recommendation": "Prefer periodic TRIM (weekly) over continuous for performance"
            },
            "enable_windows": {
                "command": "fsutil behavior set DisableDeleteNotify 0",
                "verify": "Optimize Drives should show 'Optimize' not 'Defragment'"
            }
        }
    },
    {
        "instruction": "iSCSI target disconnecting randomly",
        "response": {
            "status": "troubleshooting",
            "error": "iSCSI connection instability",
            "diagnostic_steps": [
                {"check": "Session status", "linux": "iscsiadm -m session", "windows": "iscsicli SessionList"},
                {"check": "Network stability", "command": "ping -c 100 iscsi-target"},
                {"check": "Target portal reachable", "command": "telnet iscsi-target 3260"}
            ],
            "common_causes": [
                "Network timeout settings too aggressive",
                "NIC power saving disconnecting",
                "Firewall interrupting sessions",
                "Target server overloaded"
            ],
            "solutions": {
                "increase_timeout": "iscsiadm -m node -T target-iqn -o update -n node.session.timeo.replacement_timeout -v 120",
                "disable_nic_power_save": "ethtool -s eth0 wol g or disable in Windows adapter settings",
                "multipath": "Use multiple paths for redundancy: multipathd"
            }
        }
    },
    {
        "instruction": "Rsync backup failing with permission denied errors",
        "response": {
            "status": "troubleshooting",
            "error": "rsync permission denied",
            "common_causes": [
                "Source files owned by different user",
                "Destination filesystem doesn't support permissions (FAT32)",
                "SELinux/AppArmor blocking",
                "SSH key permissions incorrect"
            ],
            "solutions": {
                "preserve_ownership": "Use sudo or run as root: sudo rsync -avz",
                "ignore_permissions": "Add --no-perms --no-owner --no-group for FAT32 destinations",
                "selinux": "Check: ls -Z source/; Temporarily: setenforce 0",
                "ssh_permissions": "chmod 600 ~/.ssh/id_rsa; chmod 700 ~/.ssh"
            },
            "complete_backup_command": "sudo rsync -avz --progress --exclude '.cache' /source/ user@backup:/dest/"
        }
    },
    {
        "instruction": "LVM volume group showing partial - missing physical volume",
        "response": {
            "status": "error_recovery",
            "error": "LVM VG partial - PV missing",
            "severity": "High - data may be at risk",
            "diagnosis": [
                {"command": "sudo vgdisplay -v", "look_for": "'partial' flag"},
                {"command": "sudo pvs -a", "look_for": "unknown device or [pvname]"},
                {"command": "sudo vgcfgrestore -l vgname", "purpose": "List available backups"}
            ],
            "recovery_options": [
                {
                    "if_disk_recoverable": "Re-attach disk, run: sudo vgchange -ay --partial vgname",
                    "note": "If disk is truly failed, you've lost data on that PV"
                },
                {
                    "remove_missing_pv": "sudo vgreduce --removemissing vgname",
                    "warning": "Data on missing PV will be lost permanently"
                },
                {
                    "restore_from_backup": "sudo vgcfgrestore -f /etc/lvm/archive/vgname_xxx.vg vgname"
                }
            ],
            "prevention": "Use mirrored LVs across PVs for redundancy"
        }
    },
    {
        "instruction": "Disk shows wrong size after replacing with larger disk",
        "response": {
            "status": "troubleshooting",
            "error": "Disk size not updated after replacement",
            "explanation": "Partition table and filesystem don't automatically expand to use new space",
            "steps": {
                "check_actual_size": "sudo fdisk -l /dev/sda or lsblk",
                "gpt_partition": {
                    "step1": "sudo gdisk /dev/sda",
                    "step2": "Use 'x' for expert mode, 'e' to relocate backup GPT",
                    "step3": "Delete and recreate partition to fill disk",
                    "warning": "Note start sector before deleting!"
                },
                "resize_filesystem": {
                    "ext4": "sudo resize2fs /dev/sda1",
                    "xfs": "sudo xfs_growfs /mountpoint",
                    "btrfs": "sudo btrfs filesystem resize max /mountpoint"
                },
                "lvm": "sudo pvresize /dev/sda1; sudo lvextend -l +100%FREE /dev/vg/lv; sudo resize2fs /dev/vg/lv"
            }
        }
    }
]

# ============================================================================
# GUARDRAIL SCENARIOS
# ============================================================================

GUARDRAILS = [
    {
        "instruction": "Format my entire disk with mkfs",
        "response": {
            "status": "blocked",
            "reason": "Potentially destructive operation",
            "warning": "Formatting a disk will PERMANENTLY DESTROY ALL DATA",
            "required_safeguards": [
                "Specify exact partition (e.g., /dev/sda1), not whole disk",
                "Verify disk with 'lsblk' first",
                "Ensure data is backed up",
                "Double-check device name (sda vs sdb matters!)"
            ],
            "safe_example": "sudo mkfs.ext4 /dev/sdb1  # Format specific partition, not sdb"
        }
    },
    {
        "instruction": "Run dd to clone my disk",
        "response": {
            "status": "caution",
            "reason": "dd can destroy data if source/destination are reversed",
            "warning": "dd operates at block level - wrong direction = total data loss",
            "safeguards": [
                "ALWAYS double-check if= (input) and of= (output)",
                "Use 'lsblk' to verify disk identities",
                "Consider using 'ddrescue' for failing disks",
                "Verify source disk is not mounted"
            ],
            "safe_command": "sudo dd if=/dev/sda of=/backup/disk.img bs=4M status=progress conv=fsync",
            "note": "Read if= as 'input FROM', of= as 'output TO'"
        }
    },
    {
        "instruction": "Delete my RAID array",
        "response": {
            "status": "blocked",
            "reason": "RAID array destruction requires careful procedure",
            "warning": "Improper RAID removal can make data unrecoverable",
            "required_steps": [
                "1. VERIFY: Ensure data is fully backed up",
                "2. UNMOUNT: Unmount all filesystems on the array",
                "3. STOP: sudo mdadm --stop /dev/mdX",
                "4. ZERO SUPERBLOCKS: sudo mdadm --zero-superblock /dev/sdX1 (each member)",
                "5. UPDATE CONFIG: Remove from /etc/mdadm/mdadm.conf",
                "6. UPDATE INITRAMFS: sudo update-initramfs -u"
            ],
            "alternative": "If keeping disks, just stop the array without zeroing superblocks"
        }
    }
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_task_response(task_data: dict) -> str:
    """Format a task as JSON response."""
    return json.dumps({
        "action": "execute_command",
        "tool": task_data["tool"],
        "command": task_data["command"],
        "explanation": task_data["explanation"]
    }, indent=2)


def format_planning_response(plan_data: dict) -> str:
    """Format planning response."""
    return json.dumps(plan_data, indent=2)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    examples = []
    
    # Linux storage tasks
    for instruction, data in LINUX_STORAGE_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": f"[Linux] {instruction}",
            "response": format_task_response(data)
        })
    
    # Windows storage tasks
    for instruction, data in WINDOWS_STORAGE_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": f"[Windows PowerShell] {instruction}",
            "response": format_task_response(data)
        })
    
    # RAID tasks
    for instruction, data in RAID_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": format_task_response(data)
        })
    
    # LVM tasks
    for instruction, data in LVM_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": format_task_response(data)
        })
    
    # Backup tasks
    for instruction, data in BACKUP_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": format_task_response(data)
        })
    
    # Filesystem tasks
    for instruction, data in FILESYSTEM_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": format_task_response(data)
        })
    
    # Planning tasks
    for task in PLANNING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_planning_response(task["response"])
        })
    
    # Concepts
    for qa in CONCEPT_QA:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": qa["instruction"],
            "response": qa["response"]
        })
    
    # Errors
    for scenario in ERROR_SCENARIOS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": json.dumps(scenario["response"], indent=2)
        })
    
    # Guardrails
    for scenario in GUARDRAILS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": json.dumps(scenario["response"], indent=2)
        })
    
    # Shuffle and write
    random.shuffle(examples)
    
    output_file = DATA_DIR / "storage_data.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"Generated {len(examples)} storage examples to {output_file}")


if __name__ == "__main__":
    main()
