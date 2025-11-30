# MT5 Service Setup Guide (Windows VM on Linux VPS)

This guide walks you through setting up a Windows VM inside your Linux VPS to run MetaTrader 5 with a FastAPI service.

## Architecture

```
┌─────────────────────────────────────────────┐
│ Linux VPS (your current server)             │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Windows VM (KVM/QEMU)               │   │
│  │  - MT5 Terminal                     │   │
│  │  - Python + FastAPI (this service)  │   │
│  │  - Port 8000 forwarded to host      │   │
│  └─────────────┬───────────────────────┘   │
│                │ HTTP                        │
│  ┌─────────────▼───────────────────────┐   │
│  │ Your AI Agent (Docker/Native)       │   │
│  │  - Calls http://host-ip:8000        │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Part 1: Install KVM on Your Linux VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install KVM and tools
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager virtinst

# Verify KVM is working
sudo kvm-ok
# Should say: "KVM acceleration can be used"

# Add your user to the libvirt group (optional, for non-root access)
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER

# Start libvirt service
sudo systemctl enable --now libvirtd
```

## Part 2: Download Windows ISO

You'll need a Windows 10 or Windows 11 ISO. Download from Microsoft's official site or use a trial version.

```bash
# Create a directory for ISOs
mkdir -p ~/vm-images

# Download Windows 10 ISO (example - use official Microsoft link)
# Option 1: Download manually from Windows website
# Option 2: Use wget if you have a direct link
cd ~/vm-images
# wget <your-windows-iso-url> -O windows10.iso
```

## Part 3: Create the Windows VM

```bash
# Create a disk image for Windows (20GB should be enough)
sudo qemu-img create -f qcow2 /var/lib/libvirt/images/windows-mt5.qcow2 20G

# Install Windows using virt-install
sudo virt-install \
  --name windows-mt5 \
  --ram 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/windows-mt5.qcow2,format=qcow2 \
  --cdrom ~/vm-images/windows10.iso \
  --os-variant win10 \
  --network network=default \
  --graphics vnc,listen=0.0.0.0,port=5900 \
  --noautoconsole

# The VM will start installing. You need to connect via VNC to complete installation.
```

## Part 4: Connect to Windows VM via VNC

### Option A: SSH Tunnel (Recommended)
```bash
# On your local machine:
ssh -L 5900:localhost:5900 root@your-vps-ip

# Then connect VNC client to localhost:5900
# Use RealVNC, TightVNC, or built-in VNC clients
```

### Option B: Direct VNC (Less Secure)
```bash
# Connect VNC client directly to your-vps-ip:5900
# Make sure firewall allows port 5900
```

Complete the Windows installation through VNC.

## Part 5: Inside the Windows VM

### 5.1 Install Python
1. Download Python 3.11 from python.org
2. Run installer, check "Add Python to PATH"

### 5.2 Install MT5
1. Download MT5 from your broker's website
2. Install and login to your trading account

### 5.3 Copy the Service Files

Transfer `main.py` and `requirements.txt` to the Windows VM:

```bash
# On Linux host, find the VM's IP
sudo virsh domifaddr windows-mt5

# Use SCP or shared folder to copy files
# Or download them directly in Windows from a file share
```

### 5.4 Install Dependencies in Windows

Open PowerShell or CMD in Windows:

```powershell
cd C:\path\to\mt5_service
pip install -r requirements.txt
```

### 5.5 Configure Environment Variables

Create a `.env` file in Windows or set environment variables:

```
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
```

### 5.6 Run the Service

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Or create a startup script to run automatically.

## Part 6: Port Forwarding from VM to Host

```bash
# On Linux host, forward port 8000 from VM to host
sudo iptables -t nat -A PREROUTING -p tcp --dport 8000 -j DNAT --to-destination <VM_IP>:8000
sudo iptables -A FORWARD -p tcp -d <VM_IP> --dport 8000 -j ACCEPT

# Make it persistent
sudo apt install iptables-persistent
sudo netfilter-persistent save
```

Or use libvirt's NAT forwarding:

```bash
sudo virsh edit windows-mt5
```

Add to `<devices>`:
```xml
<interface type='network'>
  <source network='default'/>
  <model type='virtio'/>
</interface>
```

## Part 7: Test the Service

From your Linux host:

```bash
# Get VM IP
VM_IP=$(sudo virsh domifaddr windows-mt5 | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1)

# Test health endpoint
curl http://$VM_IP:8000/health
```

## Part 8: Access from Agent

In your agent code, use:
```python
import requests

# If running in Docker, use host.docker.internal or the bridge IP
MT5_SERVICE_URL = "http://172.17.0.1:8000"  # Docker bridge
# Or use the VM IP directly
# MT5_SERVICE_URL = "http://192.168.122.xxx:8000"

response = requests.get(f"{MT5_SERVICE_URL}/health")
print(response.json())
```

## Troubleshooting

### VM not starting
```bash
# Check logs
sudo virsh list --all
sudo journalctl -xe | grep libvirt
```

### Can't connect to VNC
```bash
# Check if VNC is listening
sudo netstat -tulpn | grep 5900
```

### Port forwarding not working
```bash
# Check iptables rules
sudo iptables -t nat -L -n -v
```

### MT5 service fails to start
- Check Python installation in Windows
- Verify all dependencies installed: `pip list`
- Check MT5 is running and logged in
- Review logs in PowerShell/CMD

## Making it Persistent

### Auto-start VM on boot:
```bash
sudo virsh autostart windows-mt5
```

### Auto-start service in Windows:
Use Task Scheduler or create a Windows Service using `nssm`:
```powershell
# Download nssm.exe
# Then:
nssm install MT5Service "C:\Python311\python.exe" "-m uvicorn main:app --host 0.0.0.0 --port 8000"
```

## Resource Optimization

To minimize resources:
- Allocate 2GB RAM (can be reduced to 1GB if tight)
- Use 2 vCPUs
- Disable Windows services you don't need
- Use Windows 10 LTSC or Windows Server Core for lower overhead
