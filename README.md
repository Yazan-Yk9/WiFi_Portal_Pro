# Flexible Wi-Fi Captive Portal with Static IP & Ad-Blocking
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)


A production-ready, lightweight Docker-based Captive Portal system using Alpine Linux. It turns an Ubuntu Server with a USB Wi-Fi adapter into a fully managed, time-limited Wi-Fi Access Point featuring a Web Admin Dashboard, SQLite storage, content filtering, and automated client bypassing.

---

## 🌟 Features

* **Custom Captive Portal:** Automatically forces devices (iOS, Android, Windows) to open a splash screen to input access codes.
* **Flexible Voucher System:** Supports Permanent, 1-Hour, and 1-Day time-limited network access codes.
* **Persistent DB Storage:** Backed by an atomic SQLite database that retains state and codes across system reboots.
* **Native Whitelisting:** Auto-bypasses the portal for console hardware like PS4/Xbox via MAC-to-IP reservation with Open NAT support.
* **Integrated Ad-Blocking:** Powered by a built-in `dnsmasq` system fetching custom and upstream sinkhole blocklists.
* **Live Configuration Sync:** Edit network configurations, static IPs, and blocklists on the host in real-time without rebuilding the image.
* **Bilingual Embedded Management Shell:** Interactive terminal dashboard natively guiding administrators in English and Arabic.

---

## 📁 Directory Structure

```text
wifi-portal-pro/
├── docker-compose.yml
├── Dockerfile
├── app.py
├── nginx.conf
├── index.html
├── hostapd.conf
├── aliases.sh
└── config/
    ├── settings.env      # Hardware & Admin secrets
    ├── dnsmasq.conf      # DHCP reservations & Static IPs
    ├── blocklist.txt     # Custom domains to block
    └── whitelist.txt     # IPs to bypass the portal (PS4)
```

---

## ⚙️ Configuration

### 1. Host Variables (`config/settings.env`)
```text
WIFI_IFACE=wlan1
WAN_IFACE=eth0
GATEWAY_IP=192.168.50.1
ADMIN_PASSWORD=MySecurePass123
```

### 2. Static IP Reservations (`config/dnsmasq.conf`)
```text
interface=wlan1
dhcp-range=192.168.50.10,192.168.50.50,255.255.255.0,12h
dhcp-option=3,192.168.50.1
dhcp-option=6,192.168.50.1

# Assign Static IP to PS4 (Must match config/whitelist.txt to bypass portal)
dhcp-host=AA:BB:CC:DD:EE:FF,192.168.50.88,PS4
```

---

## 🚀 Quick Start

1. Clone your files into the workspace directory.
2. Initialize target directories and configurations:
   ```bash
   mkdir -p data config
   touch config/settings.env config/blocklist.txt config/whitelist.txt config/dnsmasq.conf
   chmod +x aliases.sh
   sudo chmod -R 777 data config
   ```
3. Run the initial clean container compile:
   ```bash
   sudo docker compose up -d --build --no-cache
   ```
4. Access the Web Admin GUI to generate vouchers: `http://192.168.50`

---

## 🛠️ Maintenance & Live Management

### Host Shell Shortcuts
Add these smart aliases to your host `~/.bashrc` file to manage the system flawlessly from your main Ubuntu shell:
```bash
alias wifi-logs="sudo docker logs -f wifi-portal-pro"
alias wifi-reload-codes="sudo docker exec wifi-portal-pro pkill -f app.py && echo '✅ Codes updated live!'"
alias wifi-reload-blocks="sudo docker exec wifi-portal-pro sh -c \"awk '{print \\\"address=/\\\"\$1\\\"/0.0.0.0/\\\"}' /etc/blocklist.txt > /etc/dnsmasq.adblock.conf && pkill -HUP dnsmasq\" && echo '✅ Blocklist applied live!'"
alias wifi-reload-whitelist="sudo docker compose up -d --build && echo '✅ Whitelist applied successfully!'"
```

### Inside the Live Container Interactive Shell
To access the built-in bilingual management shell directly inside Alpine Linux, execute:
```bash
sudo docker exec -it wifi-portal-pro sh -l
```
*Available Commands:*
* `wifi-users` : View connected clients, MACs, and lease times.
* `wifi-reload-codes` : Apply added manual backend code modifications on the fly.
* `wifi-reload-blocks` : Parse the blocklist text file and re-route traffic immediately.
* `wifi-help` : Display the interactive bilingual dashboard instructions again.

---
