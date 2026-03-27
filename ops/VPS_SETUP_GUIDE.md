# VPS Setup Guide

> Secure a fresh Ubuntu 24.04 VPS before installing Coolify and deploying your app.
> Follow these steps in order. The whole process takes ~15 minutes.
>
> **Prerequisite:** A fresh Hetzner (or any provider) Ubuntu 24.04 server with root SSH access.
> After completing this guide, continue with `ops/COOLIFY_SETUP.md`.

---

## 1. First Login & System Update

```bash
ssh root@YOUR_SERVER_IP

# Update all packages immediately
apt update && apt upgrade -y && apt autoremove -y
```

---

## 2. Create a Non-Root User

Running everything as root is dangerous. Create a dedicated user with sudo access.

```bash
adduser deploy
usermod -aG sudo deploy

# Copy root's authorized SSH keys to the new user
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

---

## 3. Harden SSH

### 3a. Disable root login and password authentication

```bash
nano /etc/ssh/sshd_config
```

Set or confirm these values:

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
X11Forwarding no
MaxAuthTries 3
LoginGraceTime 20
```

Restart SSH:

```bash
systemctl restart ssh
```

> **Before closing this session**, open a second terminal and verify you can log in as `deploy`:
> ```bash
> ssh deploy@YOUR_SERVER_IP
> ```
> Only close the root session once you've confirmed this works.

### 3b. (Optional) Change the default SSH port

Reduces automated scan noise. Not required if you have Fail2ban.

```bash
nano /etc/ssh/sshd_config
# Change: Port 22 → Port 2222 (or any non-standard port)
systemctl restart ssh
```

If you do this, remember to allow the new port through the firewall (next step) and use `ssh -p 2222 deploy@...` going forward.

---

## 4. Configure the Firewall (UFW)

```bash
# Install UFW if not present
apt install -y ufw

# Set default policy: deny all incoming, allow all outgoing
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (change 22 to your custom port if you changed it above)
ufw allow 22/tcp

# Allow HTTP and HTTPS (needed for Coolify + Traefik)
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Coolify's management UI (only during initial setup — close after)
ufw allow 8000/tcp comment 'Coolify UI — close after initial setup'

# Enable the firewall
ufw enable

# Verify
ufw status verbose
```

> After finishing Coolify setup and putting it behind a domain with SSL, close port 8000:
> ```bash
> ufw delete allow 8000/tcp
> ```

---

## 5. Install Fail2ban

Fail2ban automatically bans IPs that fail SSH logins repeatedly.

```bash
apt install -y fail2ban

# Create a local config (never edit the original .conf files)
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
backend  = systemd

[sshd]
enabled  = true
port     = ssh
logpath  = %(sshd_log)s
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Verify it's running
fail2ban-client status sshd
```

---

## 6. Enable Automatic Security Updates

```bash
apt install -y unattended-upgrades

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

# Enable security updates only (not all updates)
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

systemctl enable unattended-upgrades
systemctl start unattended-upgrades
```

---

## 7. Kernel Hardening (sysctl)

Harden the network stack against common attacks.

```bash
cat > /etc/sysctl.d/99-hardening.conf << 'EOF'
# Ignore ICMP broadcast requests (Smurf attack mitigation)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP errors
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Enable SYN flood protection
net.ipv4.tcp_syncookies = 1

# Do not accept IP source route packets
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Do not accept ICMP redirects (prevent MITM attacks)
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Do not send ICMP redirects
net.ipv4.conf.all.send_redirects = 0

# Log suspicious packets
net.ipv4.conf.all.log_martians = 1

# Protect against IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
EOF

sysctl --system
```

---

## 8. Limit Login Access (optional but recommended)

Restrict `sudo` access and SSH to specific users only.

```bash
# Only allow 'deploy' to use SSH
echo "AllowUsers deploy" >> /etc/ssh/sshd_config
systemctl restart ssh
```

---

## 9. Set Up Swap (if < 4GB RAM)

Docker builds can exhaust RAM on small servers. Swap prevents OOM kills.

```bash
# Check if swap already exists
swapon --show

# If not, create 2GB swap file
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Make it permanent
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Reduce swappiness (only use swap when really needed)
echo 'vm.swappiness=10' >> /etc/sysctl.d/99-hardening.conf
sysctl vm.swappiness=10
```

---

## 10. Verify Your Hardening

Run this checklist before proceeding to Coolify:

```bash
# SSH is working as deploy user (not root)
ssh deploy@YOUR_SERVER_IP

# Root login is blocked
ssh root@YOUR_SERVER_IP   # should be rejected

# Firewall is active with the right rules
sudo ufw status verbose

# Fail2ban is running
sudo fail2ban-client status sshd

# Auto-updates are enabled
sudo systemctl status unattended-upgrades
```

---

## 11. Install Docker (required for Coolify)

Coolify's installer does this automatically, but if you want to pre-install:

```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy
```

---

## Next Step

Your VPS is now hardened. Continue with **[Coolify Setup](./COOLIFY_SETUP.md)** to install Coolify and deploy the app.

---

## Security Checklist Summary

- [x] Non-root user with SSH key access
- [x] Root SSH login disabled
- [x] Password authentication disabled
- [x] UFW firewall configured (deny all by default)
- [x] Fail2ban protecting SSH
- [x] Automatic security updates enabled
- [x] Kernel network hardening applied
- [x] Swap configured (prevents OOM on small servers)
