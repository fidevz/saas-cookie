# VPS Setup Guide

> Secure a fresh Ubuntu 24.04 VPS before installing Coolify and deploying your app.
> Follow these steps in order. The whole process takes ~15 minutes.
>
> **Prerequisite:** A fresh Hetzner (or any provider) Ubuntu 24.04 server with root SSH access.
> After completing this guide, continue with `ops/COOLIFY_SETUP.md`.

---

## 1. First Login & System Update

When a VPS is provisioned it ships with the base OS image, which may already be days or weeks behind on security patches. The very first thing you should do — before anything else — is update all packages. Attackers actively scan for newly provisioned servers and probe known CVEs within minutes of a server going online.

```bash
ssh root@YOUR_SERVER_IP

apt update && apt upgrade -y && apt autoremove -y
```

- `apt update` refreshes the package index so apt knows what's available.
- `apt upgrade -y` installs all available updates non-interactively.
- `apt autoremove -y` removes packages that were installed as dependencies but are no longer needed — cleans up attack surface.

Reboot if the kernel was updated:

```bash
reboot
# Then reconnect: ssh root@YOUR_SERVER_IP
```

---

## 2. Create a Non-Root User

The `root` account has unrestricted access to everything on the system. If an attacker gains access to a root session — through a compromised SSH key, a misconfigured service, or a vulnerability — they own the entire server instantly with no further privilege escalation required.

The safer pattern is to use a regular user for all day-to-day operations and only invoke `sudo` when you genuinely need elevated privileges. This limits the blast radius of any mistake or breach.

```bash
# Create a user named 'deploy' — you can use any name
adduser deploy

# Grant sudo access
usermod -aG sudo deploy

# Copy root's authorized SSH keys to the new user so you can log in with the same key
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

The `rsync` command copies your `~/.ssh/authorized_keys` (which contains your public key) from root to the deploy user, preserving correct permissions. Without this step you'd be locked out when root login is disabled in the next step.

---

## 3. Harden SSH

SSH is the front door of your server. By default it listens on port 22 and allows password authentication — both of which are continuously probed by automated bots scanning the entire internet. Hardening SSH is one of the highest-impact things you can do.

### 3a. Disable root login and password authentication

```bash
nano /etc/ssh/sshd_config
```

Find and set (or add) these lines:

```
PermitRootLogin no           # Disallow root SSH entirely
PasswordAuthentication no    # Only allow SSH key login — no passwords
PubkeyAuthentication yes     # Explicitly confirm key auth is on
AuthorizedKeysFile .ssh/authorized_keys
X11Forwarding no             # Disable graphical forwarding — not needed on a server
MaxAuthTries 3               # Disconnect after 3 failed attempts (default is 6)
LoginGraceTime 20            # Give 20s to authenticate before disconnecting (default 120s)
```

**Why disable passwords?** Password brute-force attacks are trivially automated. SSH keys are cryptographically infeasible to brute-force. There is no good reason to keep passwords enabled if you have key access.

**Why disable root login?** Even with key auth, root sessions are dangerous. A typo in a root shell can destroy the system. Using `sudo` creates an intentional pause.

Restart SSH to apply:

```bash
systemctl restart ssh
```

> ⚠️ **Critical:** Before closing this terminal, open a second terminal and verify you can log in as deploy:
> ```bash
> ssh deploy@YOUR_SERVER_IP
> ```
> Only close the root session after confirming this works. If you get locked out, most VPS providers offer a browser-based emergency console.

### 3b. (Optional) Change the default SSH port

Changing from port 22 to a non-standard port (e.g. 2222) eliminates the vast majority of automated SSH probes, since most bots only scan port 22. It is not a security control on its own — a determined attacker will port-scan and find it — but it significantly reduces log noise and the surface area for opportunistic attacks.

```bash
nano /etc/ssh/sshd_config
# Change: Port 22 → Port 2222
systemctl restart ssh
```

If you change the port, remember to:
1. Allow the new port in UFW (next step) before closing your session
2. Always connect with `ssh -p 2222 deploy@YOUR_SERVER_IP` going forward
3. Update any deployment scripts or CI/CD pipelines that SSH into the server

---

## 4. Configure the Firewall (UFW)

A firewall controls which network connections are allowed into your server. Without one, every port your server opens is publicly accessible — including databases, Redis, and any development services you run. The principle here is **default deny**: block everything, then explicitly allow only what you need.

UFW (Uncomplicated Firewall) is a frontend for `iptables` that ships with Ubuntu and is much easier to manage.

```bash
apt install -y ufw

# Set default policy: block all incoming, allow all outgoing
ufw default deny incoming
ufw default allow outgoing

# Allow SSH — do this BEFORE enabling UFW or you'll lock yourself out
# If you changed the SSH port, use that port number instead of 22
ufw allow 22/tcp

# Allow HTTP and HTTPS — required for Traefik (Coolify's reverse proxy) to work
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Coolify's management UI — needed during initial setup only
# We will close this port once Coolify is behind a domain with SSL
ufw allow 8000/tcp comment 'Coolify UI — close after initial setup'

# Enable the firewall
ufw enable

# Verify the rules look correct
ufw status verbose
```

**What about Docker?** Coolify and Docker manage their own `iptables` rules for container networking. UFW and Docker can conflict in some configurations, but Coolify's installer handles this correctly — you don't need to add rules for container-to-container traffic.

> After finishing Coolify setup and accessing it via a domain over HTTPS, close port 8000:
> ```bash
> sudo ufw delete allow 8000/tcp
> ```
> There is no reason to leave Coolify's management port exposed to the internet after initial setup.

---

## 5. Install Fail2ban

Even with password auth disabled, bots will still hammer your SSH port with invalid key attempts and malformed packets. Fail2ban monitors log files and automatically bans IPs that show signs of malicious behavior (too many failed auth attempts in a short window). This protects against:

- SSH brute-force attempts
- Log file flooding
- Resource exhaustion from connection floods

```bash
apt install -y fail2ban

# Create a local override file — never edit the original .conf files directly,
# as they get overwritten on package updates
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 1h      # Ban for 1 hour on first offense
findtime = 10m     # Count failures within a 10-minute window
maxretry = 5       # Ban after 5 failures

backend  = systemd # Read logs from systemd journal (correct for Ubuntu 24.04)

[sshd]
enabled = true
port    = ssh      # Change to your custom port if you changed SSH port above
logpath = %(sshd_log)s
EOF

systemctl enable fail2ban
systemctl start fail2ban
```

Verify it's watching SSH:

```bash
fail2ban-client status sshd
```

You should see `Currently banned: 0` and `Total banned: 0` (unless someone already tried to connect). Over time, `Total banned` will grow — that's normal and expected.

To manually unban an IP (e.g. if you accidentally locked yourself out):

```bash
fail2ban-client set sshd unbanip YOUR_IP
```

---

## 6. Enable Automatic Security Updates

Security vulnerabilities are discovered and patched constantly. Manually applying updates requires discipline and is easy to forget. The `unattended-upgrades` package applies security patches automatically so your server stays protected even when you're not actively maintaining it.

**Why security updates only (not all updates)?** Full automatic upgrades can occasionally break things — a new version of a library might have a changed API, or a service might need manual config changes after upgrade. Security-only updates are lower risk because they backport fixes without changing behavior.

```bash
apt install -y unattended-upgrades

# Configure the update trigger schedule
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";    # Refresh package index daily
APT::Periodic::Unattended-Upgrade "1";      # Run upgrades daily
APT::Periodic::AutocleanInterval "7";       # Clean old package files weekly
EOF

# Configure what to upgrade and how to behave
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";   // Security patches only
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";    // Fix broken installs
Unattended-Upgrade::Remove-Unused-Dependencies "true"; // Clean up after upgrades
Unattended-Upgrade::Automatic-Reboot "false";          // Never reboot automatically
                                                        // (you control reboots)
EOF

systemctl enable unattended-upgrades
systemctl start unattended-upgrades
```

**Why `Automatic-Reboot "false"`?** Some kernel updates require a reboot to take effect. Automatic reboots on a production server are risky — they can happen at the wrong time and surprise you. Instead, check periodically:

```bash
# If this file exists, a reboot is needed to apply a kernel update
cat /var/run/reboot-required 2>/dev/null && echo "Reboot needed" || echo "No reboot needed"
```

Schedule reboots manually during low-traffic windows.

---

## 7. Kernel Hardening (sysctl)

The Linux kernel exposes many network settings that default to values optimized for compatibility rather than security. These `sysctl` settings harden the network stack against common attacks like SYN floods, IP spoofing, and ICMP-based attacks without affecting normal application traffic.

```bash
cat > /etc/sysctl.d/99-hardening.conf << 'EOF'
# --- SYN Flood Protection ---
# SYN flood attacks exhaust connection tables by sending many SYN packets without
# completing the handshake. SYN cookies allow the server to handle this gracefully.
net.ipv4.tcp_syncookies = 1

# --- IP Spoofing Protection ---
# Reverse path filtering drops packets that arrive on an interface but whose
# source address suggests they should have arrived on a different interface —
# a strong indicator of spoofed packets.
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# --- Disable IP Source Routing ---
# Source routing allows a sender to specify the route a packet takes through
# the network. Legitimate traffic never needs this; attackers use it to bypass
# network security controls.
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# --- Disable ICMP Redirects ---
# ICMP redirect messages tell the host to use a different gateway. Accepting
# them can be exploited for man-in-the-middle attacks.
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# --- Ignore Broadcast Pings ---
# Responding to broadcast pings enables Smurf attacks, where an attacker sends
# a single broadcast ping spoofed from a victim's IP, causing all hosts on the
# network to reply to the victim simultaneously.
net.ipv4.icmp_echo_ignore_broadcasts = 1

# --- Ignore Bogus ICMP Errors ---
# Some routers send invalid ICMP error responses. Logging these fills logs with
# noise; ignoring them is safe.
net.ipv4.icmp_ignore_bogus_error_responses = 1

# --- Log Suspicious Packets ---
# Log packets with impossible source addresses (martians). Useful for detecting
# misconfigured hosts or active probing on your network.
net.ipv4.conf.all.log_martians = 1
EOF

# Apply immediately (also applied automatically on every boot)
sysctl --system
```

---

## 8. Set Up Swap (if < 4GB RAM)

Swap is disk space used as overflow when physical RAM runs out. Without swap, the Linux OOM (Out of Memory) killer will start terminating processes — including your app containers — when memory is exhausted. Docker image builds are particularly memory-hungry and can easily exhaust RAM on a 2–4GB server.

Check if swap already exists:

```bash
swapon --show
free -h
```

If there's no swap (or less than 1GB), create some:

```bash
# Create a 2GB swap file
# (Use 4GB if your server has 2GB RAM or less)
fallocate -l 2G /swapfile

# Only root should be able to read/write the swap file
chmod 600 /swapfile

# Format it as swap space
mkswap /swapfile

# Enable it now
swapon /swapfile

# Make it persist across reboots
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Set swappiness to 10: only use swap when RAM is >90% full
# (default is 60, which uses swap too aggressively on SSDs)
echo 'vm.swappiness=10' >> /etc/sysctl.d/99-hardening.conf
sysctl vm.swappiness=10
```

**Why swappiness=10?** The default value of 60 means the kernel starts moving memory pages to swap when RAM is 40% full, which causes unnecessary I/O on SSD-based servers and degrades performance. A value of 10 means the kernel only uses swap as a last resort, keeping hot data in RAM.

---

## 9. Restrict SSH to Your User Only

As a final SSH hardening step, explicitly allow only the `deploy` user to SSH in. Even if another account on the server is compromised, it cannot be used to SSH in from the outside.

```bash
echo "AllowUsers deploy" >> /etc/ssh/sshd_config
systemctl restart ssh
```

---

## 10. Verify Your Hardening

Run through this checklist before proceeding to Coolify installation.

```bash
# 1. You can SSH as deploy (not root)
ssh deploy@YOUR_SERVER_IP

# 2. Root login is blocked
ssh root@YOUR_SERVER_IP
# Expected: "Permission denied (publickey)" or "Connection refused"

# 3. Firewall is active with the right ports open
sudo ufw status verbose
# Expected: 22, 80, 443, 8000 allowed — everything else denied

# 4. Fail2ban is running and watching SSH
sudo fail2ban-client status sshd
# Expected: "Status for the jail: sshd" with Jail is active: yes

# 5. Auto-updates are enabled
sudo systemctl status unattended-upgrades
# Expected: active (running)

# 6. Kernel hardening is applied
sudo sysctl net.ipv4.tcp_syncookies
# Expected: net.ipv4.tcp_syncookies = 1

# 7. Swap is active (if applicable)
swapon --show
free -h
```

---

## Next Step

Your VPS is now hardened and ready. Continue with **[Coolify Setup](./COOLIFY_SETUP.md)** to install Coolify and deploy the app.

---

## Security Checklist Summary

- [x] System packages updated on first login
- [x] Non-root `deploy` user with SSH key access
- [x] Root SSH login disabled
- [x] Password authentication disabled
- [x] UFW firewall: deny all by default, only 22/80/443 open
- [x] Fail2ban: auto-bans IPs after 5 failed SSH attempts
- [x] Unattended security updates enabled (no auto-reboot)
- [x] Kernel network hardening: SYN cookies, no ICMP redirects, rp_filter
- [x] Swap configured to prevent OOM kills during Docker builds
- [x] SSH restricted to `deploy` user only
