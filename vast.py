#!/usr/bin/env python3
"""
Vast.ai CLI Helper - FULL WRAPPER
=================================

Comprehensive wrapper around vast.ai CLI with ALL search parameters.
NOT autonomous - you're in control, agents just help run commands.

Usage: python vast.py <command> [args]
"""

import subprocess
import json
import sys
import argparse
import shutil
import os

def vast(*args, raw=True, capture=True):
    """Run vast.ai command and return output."""
    cmd = ["vastai"] + list(args)
    if raw:
        cmd.append("--raw")
    
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return None
        
        if raw and result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
        return result.stdout.strip()
    else:
        # Run interactively
        subprocess.run(cmd)
        return None


def print_table(data, columns, widths=None):
    """Print data as formatted table."""
    if not data:
        print("No results.")
        return
    
    if widths is None:
        widths = {c: max(len(c), 8) for c in columns}
    
    # Header
    header = " | ".join(f"{c:>{widths.get(c, 12)}}" for c in columns)
    print(header)
    print("-" * len(header))
    
    # Rows
    for row in data:
        values = []
        for c in columns:
            v = row.get(c, "")
            if isinstance(v, float):
                v = f"{v:.2f}"
            else:
                v = str(v)[:widths.get(c, 12)]
            values.append(f"{v:>{widths.get(c, 12)}}")
        print(" | ".join(values))


def format_gpu_ram(mb):
    """Format GPU RAM in GB."""
    if mb:
        return f"{mb / 1024:.1f}GB"
    return "?"


def format_price(dph):
    """Format price per hour."""
    if dph:
        return f"${dph:.3f}/hr"
    return "?"


# =============================================================================
# SEARCH COMMAND - FULL PARAMETERS
# =============================================================================

def cmd_search(args):
    """Search for available instances with ALL filter options."""
    
    # Build query string from all filter arguments
    query_parts = []
    
    # GPU filters
    if args.gpu_name:
        query_parts.append(f"gpu_name={args.gpu_name}")
    if args.num_gpus:
        query_parts.append(f"num_gpus={args.num_gpus}")
    if args.min_gpus:
        query_parts.append(f"num_gpus>={args.min_gpus}")
    if args.max_gpus:
        query_parts.append(f"num_gpus<={args.max_gpus}")
    if args.gpu_ram:
        query_parts.append(f"gpu_ram>={args.gpu_ram * 1024}")  # Convert GB to MB
    if args.total_flops:
        query_parts.append(f"total_flops>={args.total_flops}")
    if args.gpu_arch:
        query_parts.append(f"gpu_arch={args.gpu_arch}")
    if args.compute_cap:
        query_parts.append(f"compute_cap>={args.compute_cap}")
    if args.cuda_vers:
        query_parts.append(f"cuda_vers>={args.cuda_vers}")
    if args.driver_version:
        query_parts.append(f"driver_version>={args.driver_version}")
    
    # CPU/RAM filters
    if args.cpu_cores:
        query_parts.append(f"cpu_cores>={args.cpu_cores}")
    if args.cpu_ram:
        query_parts.append(f"cpu_ram>={args.cpu_ram * 1024}")  # Convert GB to MB
    if args.cpu_cores_effective:
        query_parts.append(f"cpu_cores_effective>={args.cpu_cores_effective}")
    
    # Storage filters
    if args.disk_space:
        query_parts.append(f"disk_space>={args.disk_space}")
    if args.disk_bw:
        query_parts.append(f"disk_bw>={args.disk_bw}")
    
    # Network filters
    if args.inet_up:
        query_parts.append(f"inet_up>={args.inet_up}")
    if args.inet_down:
        query_parts.append(f"inet_down>={args.inet_down}")
    if args.direct:
        query_parts.append("direct_port_count>=1")
    
    # Reliability/verification
    if args.reliability:
        query_parts.append(f"reliability>={args.reliability}")
    if args.verified is not None:
        query_parts.append(f"verified={'true' if args.verified else 'false'}")
    if args.rentable is not None:
        query_parts.append(f"rentable={'true' if args.rentable else 'false'}")
    if args.rented is not None:
        query_parts.append(f"rented={'true' if args.rented else 'false'}")
    
    # Price filters
    if args.max_price:
        query_parts.append(f"dph_total<={args.max_price}")
    if args.min_price:
        query_parts.append(f"dph_total>={args.min_price}")
    
    # Location filters
    if args.geolocation:
        query_parts.append(f"geolocation={args.geolocation}")
    if args.datacenter:
        query_parts.append("datacenter=true")
    
    # Duration filters
    if args.duration:
        query_parts.append(f"duration>={args.duration}")
    
    # Static IP
    if args.static_ip:
        query_parts.append("static_ip=true")
    
    # PCIe bandwidth
    if args.pcie_bw:
        query_parts.append(f"pcie_bw>={args.pcie_bw}")
    
    # DLPerf
    if args.dlperf:
        query_parts.append(f"dlperf>={args.dlperf}")
    if args.dlperf_per_dphtotal:
        query_parts.append(f"dlperf_per_dphtotal>={args.dlperf_per_dphtotal}")
    
    # Add any raw query parts
    if args.query:
        query_parts.append(args.query)
    
    # Default: show rentable verified machines
    if not query_parts:
        query_parts.append("rentable=true")
        query_parts.append("verified=true")
    
    query = " ".join(query_parts)
    
    # Build command
    cmd_args = ["search", "offers", query]
    
    if args.order:
        cmd_args.extend(["-o", args.order])
    if args.type:
        cmd_args.extend(["-t", args.type])
    if args.limit:
        cmd_args.extend(["--limit", str(args.limit)])
    if args.storage:
        cmd_args.extend(["--storage", str(args.storage)])
    
    print(f"\n🔍 Query: {query}")
    print(f"   Order: {args.order or 'default'}")
    print()
    
    data = vast(*cmd_args)
    
    if data:
        # Custom display
        print(f"Found {len(data)} offers:\n")
        
        # Define columns and widths
        cols = ["id", "gpu_name", "num_gpus", "gpu_ram", "cpu_cores", "cpu_ram", "disk_space", "dph_total", "reliability", "dlperf", "inet_down"]
        widths = {"id": 8, "gpu_name": 16, "num_gpus": 4, "gpu_ram": 8, "cpu_cores": 4, "cpu_ram": 8, "disk_space": 6, "dph_total": 10, "reliability": 6, "dlperf": 8, "inet_down": 8}
        
        # Header
        headers = ["ID", "GPU", "#GPU", "VRAM", "CPU", "RAM", "DISK", "$/HR", "REL", "DLPERF", "DOWN"]
        print(" | ".join(f"{h:>{widths[c]}}" for h, c in zip(headers, cols)))
        print("-" * 120)
        
        # Rows
        displayed = min(len(data), args.limit or 50)
        for row in data[:displayed]:
            vram = row.get("gpu_ram", 0)
            vram_str = f"{vram/1024:.0f}GB" if vram else "?"
            
            ram = row.get("cpu_ram", 0)  
            ram_str = f"{ram/1024:.0f}GB" if ram else "?"
            
            disk = row.get("disk_space", 0)
            disk_str = f"{disk:.0f}GB" if disk else "?"
            
            dph = row.get("dph_total", 0)
            dph_str = f"${dph:.4f}" if dph else "?"
            
            rel = row.get("reliability", 0)
            rel_str = f"{rel:.2f}" if rel else "?"
            
            dlp = row.get("dlperf", 0)
            dlp_str = f"{dlp:.1f}" if dlp else "-"
            
            inet = row.get("inet_down", 0)
            inet_str = f"{inet:.0f}" if inet else "?"
            
            print(f"{row.get('id', ''):>8} | {row.get('gpu_name', ''):>16} | {row.get('num_gpus', ''):>4} | {vram_str:>8} | {row.get('cpu_cores', ''):>4} | {ram_str:>8} | {disk_str:>6} | {dph_str:>10} | {rel_str:>6} | {dlp_str:>8} | {inet_str:>8}")
        
        if len(data) > displayed:
            print(f"\n... and {len(data) - displayed} more (use --limit to show more)")
        
        print(f"\n💡 To rent: python vast.py create <ID> --image <IMAGE> --disk <GB> --ssh --direct")
        print(f"   Example: python vast.py create {data[0].get('id')} --image pytorch/pytorch:latest --disk 50 --ssh --direct")
    else:
        print("No results found. Try adjusting filters.")


def cmd_search_volumes(args):
    """Search for volume storage."""
    query_parts = []
    
    if args.region:
        query_parts.append(f"region={args.region}")
    if args.disk_space:
        query_parts.append(f"disk_space>={args.disk_space}")
    
    query = " ".join(query_parts) if query_parts else "external=false"
    
    cmd_args = ["search", "volumes", query]
    if args.order:
        cmd_args.extend(["-o", args.order])
    
    data = vast(*cmd_args)
    if data:
        print(f"Found {len(data)} volume locations:\n")
        for v in data[:20]:
            print(f"  ID: {v.get('id'):>6} | Region: {v.get('region', 'unknown'):>15} | Space: {v.get('disk_space', 0):.0f}GB | Price: ${v.get('dph_total', 0):.4f}/hr")


# =============================================================================
# INSTANCE MANAGEMENT
# =============================================================================

def cmd_create(args):
    """Create/rent an instance with full options."""
    cmd_args = ["create", "instance", str(args.id)]
    
    if args.image:
        cmd_args.extend(["--image", args.image])
    if args.disk:
        cmd_args.extend(["--disk", str(args.disk)])
    if args.ssh:
        cmd_args.append("--ssh")
    if args.direct:
        cmd_args.append("--direct")
    if args.jupyter:
        cmd_args.append("--jupyter")
    if args.jupyter_dir:
        cmd_args.extend(["--jupyter-dir", args.jupyter_dir])
    if args.jupyter_lab:
        cmd_args.append("--jupyter-lab")
    if args.onstart:
        cmd_args.extend(["--onstart-cmd", args.onstart])
    if args.env:
        for e in args.env:
            cmd_args.extend(["--env", e])
    if args.label:
        cmd_args.extend(["--label", args.label])
    if args.price:
        cmd_args.extend(["--price", str(args.price)])
    if args.login:
        cmd_args.extend(["--login", args.login])
    if args.python_utf8:
        cmd_args.append("--python-utf8")
    if args.lang_utf8:
        cmd_args.append("--lang-utf8")
    if args.template_hash:
        cmd_args.extend(["--template-hash", args.template_hash])
    if args.force:
        cmd_args.append("--force")
    if args.cancel_unavail:
        cmd_args.append("--cancel-unavail")
    if args.args:
        cmd_args.extend(["--args", " ".join(args.args)])
    if args.create_from:
        cmd_args.extend(["--create-from", args.create_from])
    if args.entrypoint:
        cmd_args.extend(["--entrypoint", args.entrypoint])
    
    print(f"Creating instance from offer {args.id}...")
    result = vast(*cmd_args)
    
    if result:
        if isinstance(result, dict):
            if result.get("success"):
                instance_id = result.get("new_contract")
                print(f"\n✅ Instance created!")
                print(f"   Instance ID: {instance_id}")
                print(f"\n   Check status: python vast.py instances")
                print(f"   Get SSH:      python vast.py ssh {instance_id}")
            else:
                print(f"❌ Failed: {result}")
        else:
            print(result)
    else:
        print("❌ Failed to create instance")


def cmd_instances(args):
    """List your instances."""
    data = vast("show", "instances")
    
    if data and len(data) > 0:
        print(f"\n📦 Your instances ({len(data)}):\n")
        
        for inst in data:
            status = inst.get("actual_status", "unknown")
            status_icon = {"running": "🟢", "loading": "🟡", "exited": "🔴", "stopped": "⚫"}.get(status, "❓")
            
            gpu = inst.get("gpu_name", "?")
            num_gpus = inst.get("num_gpus", 1)
            dph = inst.get("dph_total", 0)
            
            ssh_host = inst.get("ssh_host", "")
            ssh_port = inst.get("ssh_port", "")
            
            label = inst.get("label", "")
            label_str = f" [{label}]" if label else ""
            
            print(f"  {status_icon} ID: {inst.get('id'):>8} | {gpu} x{num_gpus} | ${dph:.4f}/hr | {status}{label_str}")
            if ssh_host and ssh_port:
                print(f"      SSH: ssh -p {ssh_port} root@{ssh_host}")
            
            # Show jupyter if available
            jupyter_url = inst.get("jupyter_url", "")
            if jupyter_url:
                print(f"      Jupyter: {jupyter_url}")
            
            print()
    else:
        print("\n📦 No instances. Search and create one:")
        print("   python vast.py search --gpu-name RTX_4090")
        print("   python vast.py create <ID> --image pytorch/pytorch --disk 50 --ssh")


def cmd_instance(args):
    """Show single instance details."""
    data = vast("show", "instance", str(args.id))
    if data:
        print(json.dumps(data, indent=2))
    else:
        print(f"Instance {args.id} not found")


def cmd_start(args):
    """Start stopped instance."""
    print(f"Starting instance {args.id}...")
    result = vast("start", "instance", str(args.id))
    if result:
        print(f"✅ Instance {args.id} starting")
    else:
        print(f"❌ Failed to start")


def cmd_stop(args):
    """Stop running instance (keeps data)."""
    print(f"Stopping instance {args.id}...")
    result = vast("stop", "instance", str(args.id))
    if result:
        print(f"✅ Instance {args.id} stopped (data preserved)")
    else:
        print(f"❌ Failed to stop")


def cmd_reboot(args):
    """Reboot instance."""
    print(f"Rebooting instance {args.id}...")
    result = vast("reboot", "instance", str(args.id))
    if result:
        print(f"✅ Instance {args.id} rebooting")


def cmd_destroy(args):
    """Destroy instance (deletes data!)."""
    if not args.force:
        confirm = input(f"⚠️  Destroy instance {args.id}? This deletes ALL data! (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    result = vast("destroy", "instance", str(args.id))
    if result:
        print(f"🗑️  Instance {args.id} destroyed")


def cmd_label(args):
    """Label an instance."""
    result = vast("label", "instance", str(args.id), args.label)
    print(f"Labeled instance {args.id} as '{args.label}'")


def cmd_logs(args):
    """Get instance logs."""
    cmd_args = ["logs", str(args.id)]
    if args.tail:
        cmd_args.extend(["--tail", str(args.tail)])
    
    output = vast(*cmd_args, raw=False)
    if output:
        print(output)


def cmd_ssh(args):
    """Get SSH connection info or connect directly."""
    data = vast("show", "instance", str(args.id))
    
    if data:
        # Try direct connection first (more reliable)
        public_ip = data.get("public_ipaddr", "")
        ports = data.get("ports", {})
        ssh_direct_port = None
        if ports.get("22/tcp"):
            ssh_direct_port = ports["22/tcp"][0].get("HostPort")
        
        # Fallback to proxy
        ssh_host = data.get("ssh_host", "")
        ssh_port = data.get("ssh_port", "")
        
        if public_ip and ssh_direct_port:
            ssh_cmd = f"ssh -i ~/.ssh/id_vast root@{public_ip} -p {ssh_direct_port}"
            
            if args.connect:
                print(f"Connecting to instance {args.id}...")
                subprocess.run(["ssh", "-i", os.path.expanduser("~/.ssh/id_vast"), 
                              "-o", "StrictHostKeyChecking=no",
                              f"root@{public_ip}", "-p", str(ssh_direct_port)])
            elif args.vscode:
                print(f"Opening VS Code to instance {args.id}...")
                subprocess.run(["code", "--remote", f"ssh-remote+root@{public_ip}:{ssh_direct_port}", "/workspace"])
            else:
                print(f"\n🔗 SSH Command:")
                print(f"   {ssh_cmd}")
                print(f"\n   Connect:  python vast.py ssh {args.id} -c")
                print(f"   VS Code:  python vast.py ssh {args.id} -v")
        elif ssh_host and ssh_port:
            ssh_cmd = f"ssh -p {ssh_port} root@{ssh_host}"
            
            if args.connect:
                print(f"Connecting to instance {args.id}...")
                subprocess.run(["ssh", "-p", str(ssh_port), f"root@{ssh_host}"])
            else:
                print(f"\n🔗 SSH Command:")
                print(f"   {ssh_cmd}")
                print(f"\n   Connect: python vast.py ssh {args.id} -c")
        else:
            status = data.get("actual_status", "unknown")
            print(f"❌ SSH not available. Instance status: {status}")
            print("   Wait for instance to start or check if SSH is enabled.")
    else:
        print(f"Instance {args.id} not found")


def cmd_scp(args):
    """Get SCP connection info."""
    output = vast("scp-url", str(args.id), raw=False)
    print(f"\n📁 SCP format:\n   {output}\n")
    print("   Example: scp -P <port> local_file.txt root@<host>:/workspace/")


# =============================================================================
# DATA TRANSFER
# =============================================================================

def cmd_copy(args):
    """Copy data between instances/local."""
    cmd_args = ["copy", args.src, args.dst]
    if args.identity:
        cmd_args.extend(["-i", args.identity])
    
    print(f"Copying {args.src} -> {args.dst}...")
    output = vast(*cmd_args, raw=False)
    if output:
        print(output)


def cmd_cloud_copy(args):
    """Copy to/from cloud storage."""
    cmd_args = ["cloud", "copy",
                "--src", args.src,
                "--dst", args.dst,
                "--instance", str(args.instance),
                "--connection", str(args.connection),
                "--transfer", args.transfer]
    
    print(f"Cloud copy: {args.transfer}...")
    output = vast(*cmd_args, raw=False)
    if output:
        print(output)


# =============================================================================
# VOLUMES
# =============================================================================

def cmd_volumes(args):
    """List your volumes."""
    data = vast("show", "volumes")
    if data and len(data) > 0:
        print(f"\n💾 Your volumes ({len(data)}):\n")
        for v in data:
            print(f"  ID: {v.get('id'):>6} | {v.get('region', 'unknown')} | {v.get('disk_space', 0):.0f}GB | ${v.get('dph_total', 0):.4f}/hr")
    else:
        print("\n💾 No volumes. Create one:")
        print("   python vast.py search-volumes")
        print("   python vast.py create-volume <ID> --size <GB>")


def cmd_create_volume(args):
    """Create a persistent volume."""
    cmd_args = ["create", "volume", str(args.id), "--size", str(args.size)]
    if args.name:
        cmd_args.extend(["--name", args.name])
    
    print(f"Creating volume ({args.size}GB)...")
    result = vast(*cmd_args)
    if result:
        print(f"✅ Volume created")
        print(json.dumps(result, indent=2))


def cmd_destroy_volume(args):
    """Destroy a volume."""
    if not args.force:
        confirm = input(f"⚠️  Destroy volume {args.id}? This deletes ALL data! (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    result = vast("destroy", "volume", str(args.id))
    print(f"🗑️  Volume destroyed")


def cmd_attach_volume(args):
    """Attach volume to instance."""
    result = vast("attach", "volume", str(args.volume_id), str(args.instance_id))
    print(f"📎 Volume {args.volume_id} attached to instance {args.instance_id}")


def cmd_detach_volume(args):
    """Detach volume from instance."""
    result = vast("detach", "volume", str(args.volume_id))
    print(f"📎 Volume {args.volume_id} detached")


# =============================================================================
# TEMPLATES
# =============================================================================

def cmd_templates(args):
    """List templates."""
    data = vast("search", "templates")
    if data:
        print(f"\n📋 Templates ({len(data)}):\n")
        for t in data:
            print(f"  ID: {t.get('id'):>8} | {t.get('name', 'unnamed'):>30} | {t.get('image', '')}")


def cmd_create_template(args):
    """Create a template from current config."""
    cmd_args = ["create", "template"]
    if args.name:
        cmd_args.extend(["--name", args.name])
    if args.image:
        cmd_args.extend(["--image", args.image])
    if args.onstart:
        cmd_args.extend(["--onstart-cmd", args.onstart])
    if args.env:
        for e in args.env:
            cmd_args.extend(["--env", e])
    
    result = vast(*cmd_args)
    print(f"✅ Template created")
    if result:
        print(json.dumps(result, indent=2))


# =============================================================================
# ACCOUNT
# =============================================================================

def cmd_user(args):
    """Show account info."""
    data = vast("show", "user")
    if data:
        print(f"\n👤 Account Info:")
        print(f"   Email:   {data.get('email', '?')}")
        print(f"   Balance: ${data.get('credit', 0):.2f}")
        print(f"   API Key: {data.get('api_key', '***')[:12]}...")
        print(f"   ID:      {data.get('id', '?')}")


def cmd_invoices(args):
    """Show billing history."""
    cmd_args = ["show", "invoices"]
    if args.start:
        cmd_args.extend(["-s", args.start])
    if args.end:
        cmd_args.extend(["-e", args.end])
    if args.limit:
        cmd_args.extend(["--limit", str(args.limit)])
    
    data = vast(*cmd_args)
    if data:
        total = sum(i.get("amount", 0) for i in data)
        print(f"\n💰 Invoices: {len(data)} entries\n")
        print(f"   {'DATE':<12} | {'AMOUNT':>10} | {'TYPE':<20}")
        print("-" * 50)
        for inv in data[:args.limit or 20]:
            date = inv.get("timestamp", "")[:10]
            amt = inv.get("amount", 0)
            typ = inv.get("type", "")
            print(f"   {date:<12} | ${amt:>9.4f} | {typ:<20}")
        print("-" * 50)
        print(f"   {'TOTAL':<12} | ${abs(total):>9.2f}")


def cmd_api_keys(args):
    """List API keys."""
    data = vast("show", "api-keys")
    if data:
        print(f"\n🔑 API Keys:\n")
        for k in data:
            print(f"  ID: {k.get('id')} | {k.get('key', '')[:20]}... | {k.get('permissions', 'full')}")


def cmd_create_api_key(args):
    """Create a new API key."""
    cmd_args = ["create", "api-key"]
    if args.name:
        cmd_args.extend(["--name", args.name])
    if args.permissions:
        cmd_args.extend(["--permissions", args.permissions])
    
    result = vast(*cmd_args)
    print(f"✅ API key created")
    if result:
        print(json.dumps(result, indent=2))


def cmd_ssh_keys(args):
    """List SSH keys."""
    data = vast("show", "ssh-keys")
    if data:
        print(f"\n🔐 SSH Keys:\n")
        for k in data:
            key_preview = k.get("key", "")[:50]
            print(f"  ID: {k.get('id')} | {key_preview}...")


def cmd_add_ssh_key(args):
    """Add an SSH key."""
    # Read key from file or use provided key
    if args.file:
        with open(args.file, 'r') as f:
            key = f.read().strip()
    else:
        key = args.key
    
    result = vast("create", "ssh-key", key)
    print(f"✅ SSH key added")


def cmd_connections(args):
    """List cloud connections."""
    data = vast("show", "connections")
    if data:
        print(f"\n☁️  Cloud Connections:\n")
        for c in data:
            print(f"  ID: {c.get('id')} | {c.get('cloud_type', '')} | {c.get('label', '')}")
    else:
        print("\n☁️  No cloud connections. Add one with:")
        print("   vastai create connection --cloud-type s3 ...")


# =============================================================================
# EXECUTE
# =============================================================================

def cmd_execute(args):
    """Execute command on instance."""
    output = vast("execute", str(args.id), args.command, raw=False)
    if output:
        print(output)


# =============================================================================
# RAW PASSTHROUGH
# =============================================================================

def cmd_raw(args):
    """Pass command directly to vastai CLI."""
    cmd_args = args.args
    print(f"Running: vastai {' '.join(cmd_args)}")
    subprocess.run(["vastai"] + cmd_args)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Vast.ai CLI Helper - Full Wrapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEARCH EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Best H100s (by score):
    python vast.py search --gpu-name H100 --order score-

  Cheapest GPUs:
    python vast.py search --order dph+

  RTX 4090 under $0.50/hr:
    python vast.py search --gpu-name RTX_4090 --max-price 0.50 --order dph+

  High VRAM (48GB+):
    python vast.py search --gpu-ram 48 --order dph+

  Multi-GPU rigs:
    python vast.py search --min-gpus 4 --order dph+

  High reliability:
    python vast.py search --reliability 0.99 --gpu-name RTX_4090

  Datacenter only:
    python vast.py search --datacenter --gpu-name A100

  Best value (DLPERF per $):
    python vast.py search --order dlperf_per_dphtotal-

  Raw query (full control):
    python vast.py search "gpu_name=RTX_3090 reliability>0.95 num_gpus>=2"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTANCE MANAGEMENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Create instance:
    python vast.py create 12345 --image pytorch/pytorch:latest --disk 50 --ssh --direct

  List instances:
    python vast.py instances

  SSH to instance:
    python vast.py ssh 67890 --connect

  Stop/destroy:
    python vast.py stop 67890
    python vast.py destroy 67890

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SORT OPTIONS (--order):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  dph+              Cheapest first (price ascending)
  dph-              Most expensive first
  score-            Best overall score
  dlperf-           Best deep learning performance
  dlperf_per_dphtotal-   Best value (perf per dollar)
  reliability-      Most reliable first
  num_gpus-         Most GPUs first
  gpu_ram-          Most VRAM first
  total_flops-      Most compute first
  inet_down-        Fastest download first

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    sub = parser.add_subparsers(dest='cmd', help='Commands')
    
    # =========================================================================
    # SEARCH
    # =========================================================================
    p = sub.add_parser('search', help='Search for instances',
                       formatter_class=argparse.RawDescriptionHelpFormatter,
                       description="Search for available GPU instances with filters")
    
    # GPU filters
    gpu = p.add_argument_group('GPU Filters')
    gpu.add_argument('--gpu-name', '-g', help='GPU model (RTX_4090, H100, A100, RTX_3090, etc)')
    gpu.add_argument('--num-gpus', '-n', type=int, help='Exact number of GPUs')
    gpu.add_argument('--min-gpus', type=int, help='Minimum number of GPUs')
    gpu.add_argument('--max-gpus', type=int, help='Maximum number of GPUs')
    gpu.add_argument('--gpu-ram', type=float, help='Minimum GPU VRAM in GB')
    gpu.add_argument('--total-flops', type=float, help='Minimum total TFLOPS')
    gpu.add_argument('--gpu-arch', help='GPU architecture (ampere, hopper, ada)')
    gpu.add_argument('--compute-cap', type=float, help='Min compute capability (e.g., 8.0)')
    gpu.add_argument('--cuda-vers', type=float, help='Min CUDA version')
    gpu.add_argument('--driver-version', help='Min driver version')
    
    # CPU/RAM filters
    sys_grp = p.add_argument_group('System Filters')
    sys_grp.add_argument('--cpu-cores', type=int, help='Minimum CPU cores')
    sys_grp.add_argument('--cpu-ram', type=float, help='Minimum RAM in GB')
    sys_grp.add_argument('--cpu-cores-effective', type=float, help='Min effective CPU cores')
    
    # Storage filters  
    stor = p.add_argument_group('Storage Filters')
    stor.add_argument('--disk-space', type=float, help='Minimum disk space GB')
    stor.add_argument('--disk-bw', type=float, help='Minimum disk bandwidth MB/s')
    stor.add_argument('--storage', type=float, help='Required storage GB for offer')
    
    # Network filters
    net = p.add_argument_group('Network Filters')
    net.add_argument('--inet-up', type=float, help='Minimum upload Mbps')
    net.add_argument('--inet-down', type=float, help='Minimum download Mbps')
    net.add_argument('--direct', action='store_true', help='Direct port connection required')
    net.add_argument('--static-ip', action='store_true', help='Static IP required')
    
    # Quality filters
    qual = p.add_argument_group('Quality Filters')
    qual.add_argument('--reliability', '-r', type=float, help='Minimum reliability (0-1, e.g., 0.95)')
    qual.add_argument('--verified', type=lambda x: x.lower() == 'true', help='Verified hosts only')
    qual.add_argument('--rentable', type=lambda x: x.lower() == 'true', default=None, help='Rentable machines')
    qual.add_argument('--rented', type=lambda x: x.lower() == 'true', default=None, help='Show rented machines')
    qual.add_argument('--datacenter', action='store_true', help='Datacenter machines only')
    
    # Price filters
    price = p.add_argument_group('Price Filters')
    price.add_argument('--max-price', type=float, help='Maximum $/hr')
    price.add_argument('--min-price', type=float, help='Minimum $/hr')
    
    # Performance filters
    perf = p.add_argument_group('Performance Filters')
    perf.add_argument('--dlperf', type=float, help='Minimum DLPerf score')
    perf.add_argument('--dlperf-per-dphtotal', type=float, help='Min DLPerf per dollar')
    perf.add_argument('--pcie-bw', type=float, help='Minimum PCIe bandwidth')
    
    # Location
    loc = p.add_argument_group('Location Filters')
    loc.add_argument('--geolocation', help='Location code (e.g., US, EU)')
    loc.add_argument('--duration', type=float, help='Min rental duration (days)')
    
    # Output options
    out = p.add_argument_group('Output Options')
    out.add_argument('-o', '--order', help='Sort order (dph+, score-, dlperf-, reliability-, etc)')
    out.add_argument('-t', '--type', choices=['on-demand', 'bid', 'reserved', 'interruptible'], default='on-demand')
    out.add_argument('-l', '--limit', type=int, default=30, help='Max results to show')
    out.add_argument('query', nargs='?', default='', help='Raw query string (advanced)')
    
    p.set_defaults(func=cmd_search)
    
    # search-volumes
    p = sub.add_parser('search-volumes', help='Search for volume storage')
    p.add_argument('--region', help='Region filter')
    p.add_argument('--disk-space', type=float, help='Min disk space GB')
    p.add_argument('-o', '--order', help='Sort order')
    p.set_defaults(func=cmd_search_volumes)
    
    # =========================================================================
    # CREATE
    # =========================================================================
    p = sub.add_parser('create', help='Create/rent instance')
    p.add_argument('id', type=int, help='Offer ID from search')
    p.add_argument('--image', '-i', required=True, help='Docker image')
    p.add_argument('--disk', '-d', type=int, default=20, help='Disk size GB')
    p.add_argument('--ssh', action='store_true', help='Enable SSH')
    p.add_argument('--direct', action='store_true', help='Direct port connection')
    p.add_argument('--jupyter', action='store_true', help='Enable Jupyter')
    p.add_argument('--jupyter-dir', help='Jupyter working directory')
    p.add_argument('--jupyter-lab', action='store_true', help='Use JupyterLab')
    p.add_argument('--onstart', help='On-start command')
    p.add_argument('--env', action='append', help='Environment vars (KEY=value)')
    p.add_argument('--label', help='Instance label')
    p.add_argument('--price', type=float, help='Bid price (for bid instances)')
    p.add_argument('--login', help='Docker registry login')
    p.add_argument('--python-utf8', action='store_true', help='Set Python UTF-8 mode')
    p.add_argument('--lang-utf8', action='store_true', help='Set LANG to UTF-8')
    p.add_argument('--template-hash', help='Use template by hash')
    p.add_argument('--force', action='store_true', help='Force create')
    p.add_argument('--cancel-unavail', action='store_true', help='Cancel if unavailable')
    p.add_argument('--args', nargs='*', help='Docker args')
    p.add_argument('--create-from', help='Create from snapshot')
    p.add_argument('--entrypoint', help='Docker entrypoint')
    p.set_defaults(func=cmd_create)
    
    # =========================================================================
    # INSTANCES
    # =========================================================================
    p = sub.add_parser('instances', aliases=['ls'], help='List your instances')
    p.set_defaults(func=cmd_instances)
    
    p = sub.add_parser('instance', help='Show instance details')
    p.add_argument('id', type=int)
    p.set_defaults(func=cmd_instance)
    
    p = sub.add_parser('start', help='Start instance')
    p.add_argument('id', type=int)
    p.set_defaults(func=cmd_start)
    
    p = sub.add_parser('stop', help='Stop instance')
    p.add_argument('id', type=int)
    p.set_defaults(func=cmd_stop)
    
    p = sub.add_parser('reboot', help='Reboot instance')
    p.add_argument('id', type=int)
    p.set_defaults(func=cmd_reboot)
    
    p = sub.add_parser('destroy', help='Destroy instance')
    p.add_argument('id', type=int)
    p.add_argument('-f', '--force', action='store_true')
    p.set_defaults(func=cmd_destroy)
    
    p = sub.add_parser('label', help='Label instance')
    p.add_argument('id', type=int)
    p.add_argument('label')
    p.set_defaults(func=cmd_label)
    
    p = sub.add_parser('logs', help='Get logs')
    p.add_argument('id', type=int)
    p.add_argument('--tail', type=int, default=100)
    p.set_defaults(func=cmd_logs)
    
    p = sub.add_parser('ssh', help='SSH info/connect')
    p.add_argument('id', type=int)
    p.add_argument('--connect', '-c', action='store_true', help='Connect directly')
    p.add_argument('--vscode', '-v', action='store_true', help='Open in VS Code')
    p.set_defaults(func=cmd_ssh)
    
    p = sub.add_parser('scp', help='SCP info')
    p.add_argument('id', type=int)
    p.set_defaults(func=cmd_scp)
    
    # =========================================================================
    # DATA TRANSFER
    # =========================================================================
    p = sub.add_parser('copy', help='Copy data')
    p.add_argument('src', help='Source (local:./path or ID:/path)')
    p.add_argument('dst', help='Destination')
    p.add_argument('-i', '--identity', help='SSH key')
    p.set_defaults(func=cmd_copy)
    
    p = sub.add_parser('cloud-copy', help='Cloud storage copy')
    p.add_argument('--src', required=True)
    p.add_argument('--dst', required=True)
    p.add_argument('--instance', type=int, required=True)
    p.add_argument('--connection', type=int, required=True)
    p.add_argument('--transfer', choices=['Instance To Cloud', 'Cloud To Instance'], required=True)
    p.set_defaults(func=cmd_cloud_copy)
    
    # =========================================================================
    # VOLUMES
    # =========================================================================
    p = sub.add_parser('volumes', help='List volumes')
    p.set_defaults(func=cmd_volumes)
    
    p = sub.add_parser('create-volume', help='Create volume')
    p.add_argument('id', type=int, help='Volume offer ID')
    p.add_argument('--size', type=int, required=True, help='Size in GB')
    p.add_argument('--name', help='Volume name')
    p.set_defaults(func=cmd_create_volume)
    
    p = sub.add_parser('destroy-volume', help='Destroy volume')
    p.add_argument('id', type=int)
    p.add_argument('-f', '--force', action='store_true')
    p.set_defaults(func=cmd_destroy_volume)
    
    p = sub.add_parser('attach-volume', help='Attach volume')
    p.add_argument('volume_id', type=int)
    p.add_argument('instance_id', type=int)
    p.set_defaults(func=cmd_attach_volume)
    
    p = sub.add_parser('detach-volume', help='Detach volume')
    p.add_argument('volume_id', type=int)
    p.set_defaults(func=cmd_detach_volume)
    
    # =========================================================================
    # TEMPLATES
    # =========================================================================
    p = sub.add_parser('templates', help='List templates')
    p.set_defaults(func=cmd_templates)
    
    p = sub.add_parser('create-template', help='Create template')
    p.add_argument('--name', help='Template name')
    p.add_argument('--image', help='Docker image')
    p.add_argument('--onstart', help='On-start command')
    p.add_argument('--env', action='append', help='Environment vars')
    p.set_defaults(func=cmd_create_template)
    
    # =========================================================================
    # ACCOUNT
    # =========================================================================
    p = sub.add_parser('user', help='Account info')
    p.set_defaults(func=cmd_user)
    
    p = sub.add_parser('invoices', help='Billing history')
    p.add_argument('-s', '--start', help='Start date')
    p.add_argument('-e', '--end', help='End date')
    p.add_argument('-l', '--limit', type=int, default=20)
    p.set_defaults(func=cmd_invoices)
    
    p = sub.add_parser('api-keys', help='List API keys')
    p.set_defaults(func=cmd_api_keys)
    
    p = sub.add_parser('create-api-key', help='Create API key')
    p.add_argument('--name', help='Key name')
    p.add_argument('--permissions', help='Permissions')
    p.set_defaults(func=cmd_create_api_key)
    
    p = sub.add_parser('ssh-keys', help='List SSH keys')
    p.set_defaults(func=cmd_ssh_keys)
    
    p = sub.add_parser('add-ssh-key', help='Add SSH key')
    p.add_argument('--file', '-f', help='Key file path')
    p.add_argument('--key', '-k', help='Key string')
    p.set_defaults(func=cmd_add_ssh_key)
    
    p = sub.add_parser('connections', help='Cloud connections')
    p.set_defaults(func=cmd_connections)
    
    # =========================================================================
    # EXECUTE
    # =========================================================================
    p = sub.add_parser('exec', help='Execute on instance')
    p.add_argument('id', type=int)
    p.add_argument('command')
    p.set_defaults(func=cmd_execute)
    
    # =========================================================================
    # RAW
    # =========================================================================
    p = sub.add_parser('raw', help='Raw vastai command')
    p.add_argument('args', nargs='*', help='Args to pass to vastai')
    p.set_defaults(func=cmd_raw)
    
    # Parse
    args = parser.parse_args()
    
    if not args.cmd:
        parser.print_help()
        return
    
    # Check vastai installed
    if not shutil.which("vastai"):
        print("❌ vastai CLI not found. Install with: pip install vastai")
        print("   Then set API key: vastai set api-key <YOUR_KEY>")
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
