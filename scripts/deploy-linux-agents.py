#!/usr/bin/env python3
"""Deploy FunnelCloud agents to Linux hosts using paramiko for SSH automation."""

import paramiko
import os
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
SECRETS = WORKSPACE / "secrets"
FUNNELCLOUD = WORKSPACE / "layers" / "agents" / "FunnelCloud"
PUBLISH_LINUX = FUNNELCLOUD / "publish-linux"
CERTS = FUNNELCLOUD / "certs"

def get_ssh_password():
    return (SECRETS / "ssh.txt").read_text().strip()

def get_ssh_client(host: str, user: str = "ian") -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Use password auth (simpler and works reliably)
    password = get_ssh_password()
    client.connect(host, username=user, password=password, timeout=10, allow_agent=False, look_for_keys=False)
    print(f"[✓] Connected to {host}")
    return client

def run_cmd(client: paramiko.SSHClient, cmd: str, sudo: bool = False) -> str:
    if sudo:
        password = get_ssh_password()
        # Use bash -c with heredoc-style sudo
        full_cmd = f"sudo -S bash -c '{cmd}'"
        stdin, stdout, stderr = client.exec_command(full_cmd, get_pty=True)
        stdin.write(password + "\n")
        stdin.flush()
    else:
        stdin, stdout, stderr = client.exec_command(cmd)
    
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    errors = stderr.read().decode()
    
    if exit_code != 0:
        # Filter out sudo password prompt from errors
        errors = "\n".join(l for l in errors.split("\n") if "[sudo]" not in l and "password" not in l.lower())
        if errors.strip():
            print(f"    [!] {errors.strip()}")
    
    return output.strip()

def setup_ssh_key(host: str, user: str = "ian"):
    """Copy SSH public key to remote host for future passwordless access."""
    key_path = Path.home() / ".ssh" / "id_rsa.pub"
    if not key_path.exists():
        print(f"[!] No SSH public key at {key_path}")
        return
    
    pubkey = key_path.read_text().strip()
    client = get_ssh_client(host, user)
    
    try:
        run_cmd(client, "mkdir -p ~/.ssh && chmod 700 ~/.ssh")
        
        # Check if key already exists
        existing = run_cmd(client, "cat ~/.ssh/authorized_keys 2>/dev/null || echo ''")
        if pubkey in existing:
            print(f"[✓] SSH key already installed on {host}")
        else:
            run_cmd(client, f"echo '{pubkey}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys")
            print(f"[✓] SSH key installed on {host}")
    finally:
        client.close()

def scp_directory(client: paramiko.SSHClient, local_dir: Path, remote_dir: str):
    """Copy directory contents to remote host."""
    sftp = client.open_sftp()
    
    try:
        # Create remote directory
        try:
            sftp.mkdir(remote_dir)
        except:
            pass
        
        for item in local_dir.iterdir():
            remote_path = f"{remote_dir}/{item.name}"
            if item.is_file():
                sftp.put(str(item), remote_path)
            elif item.is_dir():
                scp_directory_recursive(sftp, item, remote_path)
    finally:
        sftp.close()

def scp_directory_recursive(sftp, local_dir: Path, remote_dir: str):
    """Recursively copy directory."""
    try:
        sftp.mkdir(remote_dir)
    except:
        pass
    
    for item in local_dir.iterdir():
        remote_path = f"{remote_dir}/{item.name}"
        if item.is_file():
            sftp.put(str(item), remote_path)
        elif item.is_dir():
            scp_directory_recursive(sftp, item, remote_path)

def deploy_agent(host: str, user: str = "ian", install_path: str = "/opt/funnelcloud"):
    """Deploy FunnelCloud agent to a Linux host."""
    agent_id = host.split(".")[0]
    print(f"\n{'='*60}")
    print(f"  Deploying FunnelCloud Agent to {host}")
    print(f"  Agent ID: {agent_id}")
    print(f"{'='*60}\n")
    
    # Setup SSH key first
    setup_ssh_key(host, user)
    
    client = get_ssh_client(host, user)
    
    try:
        # Stop existing service
        print("[>] Stopping existing service...")
        run_cmd(client, "systemctl stop funnelcloud-agent 2>/dev/null || true", sudo=True)
        print("    [OK] Service stopped")
        
        # Create staging directory
        print("[>] Creating staging directory...")
        run_cmd(client, "rm -rf /tmp/fc-staging && mkdir -p /tmp/fc-staging")
        print("    [OK] Staging ready")
        
        # Copy agent files
        print("[>] Copying agent files (this may take a minute)...")
        scp_directory(client, PUBLISH_LINUX, "/tmp/fc-staging")
        print("    [OK] Files copied")
        
        # Copy certificates if they exist
        agent_certs = CERTS / "agents" / agent_id
        ca_cert = CERTS / "ca" / "ca.crt"
        
        if agent_certs.exists() and ca_cert.exists():
            print("[>] Copying certificates...")
            run_cmd(client, "mkdir -p /tmp/fc-staging/Certificates")
            sftp = client.open_sftp()
            sftp.put(str(ca_cert), "/tmp/fc-staging/Certificates/ca.crt")
            for cert_file in agent_certs.glob("*"):
                sftp.put(str(cert_file), f"/tmp/fc-staging/Certificates/{cert_file.name}")
            sftp.close()
            print("    [OK] Certificates copied")
        else:
            print("[>] Generating certificates...")
            # Generate certs using the script logic
            agent_certs.mkdir(parents=True, exist_ok=True)
            # For now, skip cert generation - use insecure mode
            print("    [!] Running in insecure mode (no mTLS)")
        
        # Create systemd service file
        service_content = f"""[Unit]
Description=FunnelCloud Agent - {agent_id}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
WorkingDirectory={install_path}
ExecStart={install_path}/FunnelCloud.Agent
Restart=always
RestartSec=10
Environment=FUNNEL_AGENT_ID={agent_id}
Environment=FUNNEL_CERT_PATH={install_path}/Certificates/agent.pfx
Environment=FUNNEL_CERT_PASSWORD=funnelcloud
Environment=FUNNEL_CA_PATH={install_path}/Certificates/ca.crt
StandardOutput=journal
StandardError=journal
SyslogIdentifier=funnelcloud-agent

[Install]
WantedBy=multi-user.target
"""
        sftp = client.open_sftp()
        with sftp.open("/tmp/fc-staging/funnelcloud-agent.service", "w") as f:
            f.write(service_content)
        sftp.close()
        
        # Install - run commands one at a time for better error handling
        print("[>] Installing agent...")
        
        # Run install commands separately to avoid quote escaping issues
        install_commands = [
            f"mkdir -p {install_path} {install_path}/logs",
            f"cp -r /tmp/fc-staging/* {install_path}/",
            f"chmod +x {install_path}/FunnelCloud.Agent",
            f"chown -R {user}:{user} {install_path}",
            f"cp {install_path}/funnelcloud-agent.service /etc/systemd/system/",
            "systemctl daemon-reload",
            "systemctl enable funnelcloud-agent",
            "systemctl restart funnelcloud-agent",
        ]
        
        for cmd in install_commands:
            run_cmd(client, cmd, sudo=True)
        
        print("    [OK] Agent installed")
        
        # Cleanup
        run_cmd(client, "rm -rf /tmp/fc-staging")
        
        # Verify
        print("[>] Verifying...")
        import time
        time.sleep(3)
        status = run_cmd(client, "systemctl is-active funnelcloud-agent")
        if "active" in status:
            print("    [OK] Service is running!")
        else:
            print(f"    [!] Status: {status}")
        
        # Show recent logs
        print("\n[>] Recent logs:")
        logs = run_cmd(client, "journalctl -u funnelcloud-agent -n 5 --no-pager 2>/dev/null || echo 'No logs yet'", sudo=True)
        for line in logs.split("\n")[-5:]:
            if line.strip():
                print(f"    {line}")
        
        print(f"\n{'='*60}")
        print(f"  Deployment Complete: {host}")
        print(f"{'='*60}")
        print(f"\nPorts: UDP 41420 (discovery), TCP 41235 (gRPC), TCP 41236 (HTTP)")
        print(f"\nCommands:")
        print(f"  sudo systemctl status funnelcloud-agent")
        print(f"  sudo journalctl -u funnelcloud-agent -f")
        
    finally:
        client.close()

def check_discovery(hosts: list[str]):
    """Check if agents are discoverable via multicast/gossip."""
    print(f"\n{'='*60}")
    print("  Checking Agent Discovery")
    print(f"{'='*60}\n")
    
    for host in hosts:
        agent_id = host.split(".")[0]
        try:
            import urllib.request
            url = f"http://{host}:41421/gossip"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read().decode()
                print(f"[✓] {agent_id}: Gossip endpoint responding")
                print(f"    {data[:100]}...")
        except Exception as e:
            print(f"[!] {agent_id}: Gossip not responding - {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deploy-linux-agents.py <host1> [host2] ...")
        print("       python deploy-linux-agents.py postfix01 plex01")
        sys.exit(1)
    
    hosts = sys.argv[1:]
    
    for host in hosts:
        deploy_agent(host)
    
    # Check discovery
    check_discovery(hosts)
