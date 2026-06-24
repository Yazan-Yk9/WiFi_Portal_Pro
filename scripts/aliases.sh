#!/bin/sh
# ===================================================================
# 🎯 Smart Aliases - WIFI Portal Pro Management
# ===================================================================

# ===================================================================
# 📱 User Management
# ===================================================================
export PS1="📡 \[\033[01;32m\][Wifi-Portal-Pro]:\[\033[01;34m\]\w\[\033[00m\]# "
# Show connected devices
alias wifi-users="echo '📱 Connected Devices:'; echo '----------------------------------------'; cat /var/lib/misc/dnsmasq.leases | awk '{print \"IP: \"\$3\" | MAC: \"\$2\" | Expires: \"\$1}'"

# Show network statistics
alias wifi-stats="echo '📊 Network Statistics:'; echo '----------------------------------------'; echo \"Total Vouchers: \$(sqlite3 /app/data/portal.db 'SELECT COUNT(*) FROM vouchers')\"; echo \"Active: \$(sqlite3 /app/data/portal.db 'SELECT COUNT(*) FROM vouchers WHERE status=\"active\"')\"; echo \"Used: \$(sqlite3 /app/data/portal.db 'SELECT COUNT(*) FROM vouchers WHERE status=\"used\"')\"; echo \"Expired: \$(sqlite3 /app/data/portal.db 'SELECT COUNT(*) FROM vouchers WHERE status=\"expired\"')\"; echo \"\"; echo \"Connected Devices: \$(cat /var/lib/misc/dnsmasq.leases | wc -l)\""

# Show interface status
alias wifi-iface="echo '📡 Interface Status:'; echo '----------------------------------------'; ip addr show | grep -E '^[0-9]|inet ' | grep -v '127.0.0.1'"

# ===================================================================
# 🗄️ Voucher Management
# ===================================================================

# Show all vouchers
alias wifi-codes="echo '📋 All Vouchers:'; echo '----------------------------------------'; sqlite3 /app/data/portal.db 'SELECT code, duration, status, expiry, used_by_ip FROM vouchers ORDER BY created_at DESC;' | column -t -s '|'"

# Show active vouchers / عرض الأكواد النشطة
alias wifi-active="echo '✅ Active Vouchers:'; echo '----------------------------------------'; sqlite3 /app/data/portal.db 'SELECT code, duration, created_at FROM vouchers WHERE status=\"active\";' | column -t -s '|'"

# Show used vouchers / عرض الأكواد المستخدمة
alias wifi-used="echo '🟡 Used Vouchers:'; echo '----------------------------------------'; sqlite3 /app/data/portal.db 'SELECT code, used_by_ip, expiry FROM vouchers WHERE status=\"used\";' | column -t -s '|'"

# Show expired vouchers / عرض الأكواد المنتهية
alias wifi-expired="echo '🔴 Expired Vouchers:'; echo '----------------------------------------'; sqlite3 /app/data/portal.db 'SELECT code, expiry FROM vouchers WHERE status=\"expired\";' | column -t -s '|'"

# Generate new voucher / توليد كود جديد
alias wifi-gen="echo '⚡ Generate New Voucher:'; echo '----------------------------------------'; read -p 'Duration (1h/2h/4h/8h/1d/2d/1w/1m/permanent): ' duration; curl -X POST http://localhost:5000/admin/generate -H 'Cookie: admin_session=$ADMIN_PASSWORD' -d \"duration=\$duration\" 2>/dev/null | grep -o 'الكود: [A-Z0-9]*' || echo '❌ Failed to generate code'"

# Delete voucher / حذف كود
alias wifi-del="echo '🗑️ Delete Voucher:'; echo '----------------------------------------'; read -p 'Enter voucher code: ' code; sqlite3 /app/data/portal.db 'DELETE FROM vouchers WHERE code=\"'\$code'\";'; echo \"✅ Deleted voucher: \$code\""

# ===================================================================
# 🛡️ Firewall Management
# ===================================================================

# Show firewall rules
alias wifi-firewall="echo '🛡️ Firewall Rules:'; echo '----------------------------------------'; echo '--- FORWARD ---'; iptables -L FORWARD -v -n; echo ''; echo '--- NAT ---'; iptables -t nat -L PREROUTING -v -n"

# Clean user rules
alias wifi-clean-users="echo '🧹 Cleaning User Rules:'; echo '----------------------------------------'; iptables -D FORWARD -s 192.168.50.0/24 -j DROP 2>/dev/null; while iptables -D FORWARD -s 192.168.50.0/24 -j ACCEPT 2>/dev/null; do :; done; echo '✅ All user rules cleaned'"

# Add user manually
alias wifi-add-user="echo '➕ Add User Manually:'; echo '----------------------------------------'; read -p 'Enter IP address: ' ip; iptables -I FORWARD -s \$ip -j ACCEPT; iptables -t nat -I PREROUTING -s \$ip -j ACCEPT; echo \"✅ Added user: \$ip\""

# Remove user manually
alias wifi-remove-user="echo '➖ Remove User:'; echo '----------------------------------------'; read -p 'Enter IP address: ' ip; iptables -D FORWARD -s \$ip -j ACCEPT 2>/dev/null; iptables -t nat -D PREROUTING -s \$ip -j ACCEPT 2>/dev/null; echo \"✅ Removed user: \$ip\""

# ===================================================================
# 🔄 Service Management
# ===================================================================

# Restart all services
alias wifi-restart="echo '🔄 Restarting Services:'; echo '----------------------------------------'; pkill -f app.py; pkill -HUP nginx; pkill -HUP hostapd; pkill -HUP dnsmasq; sleep 2; python3 /app/app.py & nginx & hostapd /etc/hostapd/hostapd.conf & dnsmasq --no-daemon --conf-file=/etc/dnsmasq.conf --addn-hosts=/etc/dnsmasq.portal.conf --addn-hosts=/etc/dnsmasq.adblock.conf & echo '✅ Services restarted'"

# Reload DNS
alias wifi-reload-dns="echo '🔄 Reloading DNS:'; echo '----------------------------------------'; pkill -HUP dnsmasq; echo '✅ DNS reloaded'"

# Reload Hostapd
alias wifi-reload-hostapd="echo '🔄 Reloading Hostapd:'; echo '----------------------------------------'; pkill -HUP hostapd; echo '✅ Hostapd reloaded'"

# ===================================================================
# 🛑 Blocklist Management
# ===================================================================

# Update blocklist
alias wifi-reload-blocks="echo '🛑 Updating Blocklist:'; echo '----------------------------------------'; if [ -f /etc/blocklist.txt ]; then awk '{gsub(/^[[:space:]]+|[[:space:]]+$/, \"\", \$0); if (\$0 !~ /^#/ && \$0 != \"\") print \"address=/\"\$1\"/0.0.0.0\"}' /etc/blocklist.txt > /etc/dnsmasq.adblock.conf; pkill -HUP dnsmasq; echo '✅ Blocklist updated'; else echo '⚠️ No blocklist found'; fi"

# Update whitelist
alias wifi-reload-whitelist="echo '✅ Updating Whitelist:'; echo '----------------------------------------'; if [ -f /etc/whitelist.txt ]; then while read -r ip; do if [ ! -z \"\$ip\" ] && [ \"\$ip\" != \"0.0.0.0\" ]; then iptables -I FORWARD -s \"\$ip\" -j ACCEPT 2>/dev/null; fi; done < /etc/whitelist.txt; echo '✅ Whitelist applied'; else echo '⚠️ No whitelist found'; fi"

# ===================================================================
# 📊 Monitoring
# ===================================================================

# View live logs
alias wifi-logs="echo '📜 Live Logs:'; echo '----------------------------------------'; tail -f /var/log/nginx/access.log /var/log/nginx/error.log"

# Live monitoring
alias wifi-monitor="echo '📊 Live Monitoring:'; echo '----------------------------------------'; watch -n 2 'echo \"Connected Devices:\" && cat /var/lib/misc/dnsmasq.leases | wc -l && echo \"\" && echo \"Active Rules:\" && iptables -L FORWARD -v -n | grep ACCEPT | wc -l'"

# Quick status
alias wifi-quick="echo '⚡ Quick Status:'; echo '----------------------------------------'; echo \"Connected: \$(cat /var/lib/misc/dnsmasq.leases | wc -l) devices\"; echo \"Active Vouchers: \$(sqlite3 /app/data/portal.db 'SELECT COUNT(*) FROM vouchers WHERE status=\"active\"')\"; echo \"Used Vouchers: \$(sqlite3 /app/data/portal.db 'SELECT COUNT(*) FROM vouchers WHERE status=\"used\"')\"; echo \"Expired: \$(sqlite3 /app/data/portal.db 'SELECT COUNT(*) FROM vouchers WHERE status=\"expired\"')\"; echo \"\"; echo \"Latest 3 connections:\"; cat /var/lib/misc/dnsmasq.leases | tail -3 | awk '{print \"  \"\$3\" - \"\$2}'"

# ===================================================================
# 🔧 Maintenance
# ===================================================================

# Clean database
alias wifi-cleanup-db="echo '🧹 Database Cleanup:'; echo '----------------------------------------'; sqlite3 /app/data/portal.db 'DELETE FROM vouchers WHERE status=\"expired\" AND datetime(expiry) < datetime(\"now\", \"-7 days\");'; echo '✅ Old expired vouchers removed'"

# Backup database
alias wifi-backup="echo '💾 Database Backup:'; echo '----------------------------------------'; cp /app/data/portal.db /app/data/portal.db.backup.\$(date +%Y%m%d_%H%M%S); echo '✅ Backup created'"

# Show database size
alias wifi-db-size="echo '📊 Database Size:'; echo '----------------------------------------'; ls -lh /app/data/portal.db | awk '{print \"Size: \"\$5}'"

# ===================================================================
# ℹ️ System Info
# ===================================================================

# Show system information
alias wifi-info="echo 'ℹ️ System Info:'; echo '----------------------------------------'; echo \"Hostname: \$(hostname)\"; echo \"Uptime: \$(uptime -p)\"; echo \"Memory: \$(free -h | grep Mem | awk '{print \$3\"/\"\$2}')\"; echo \"Disk: \$(df -h / | tail -1 | awk '{print \$3\"/\"\$2\" (\"\$5\")\"}')\"; echo \"WiFi Interface: \$WIFI_IFACE\"; echo \"Gateway IP: \$GATEWAY_IP\""

# ===================================================================
# 🎨 Welcome Dashboard
# ===================================================================

# Show help menu
alias wifi-help="sh /etc/profile.d/aliases.sh"

# Clear and show welcome screen
clear
echo "=================================================================="
echo "🎯 CAPTIVE PORTAL MANAGEMENT SYSTEM"
echo "=================================================================="
echo ""
echo "🌐 NETWORK INFO:"
echo "  Interface: $WIFI_IFACE"
echo "  Gateway: $GATEWAY_IP"
echo "  Connected: $(cat /var/lib/misc/dnsmasq.leases 2>/dev/null | wc -l) devices"
echo ""
echo "📋 AVAILABLE COMMANDS:"
echo ""
echo "  ┌─────────────────────────────────────────────────────────────┐"
echo "  │  📱 USER MANAGEMENT                                         │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  wifi-users        │ Connected devices                      │"
echo "  │  wifi-stats        │ Network statistics                     │"
echo "  │  wifi-codes        │ All vouchers                           │"
echo "  │  wifi-active       │ Active vouchers                        │"
echo "  │  wifi-used         │ Used vouchers                          │"
echo "  │  wifi-expired      │ Expired vouchers                       │"
echo "  │  wifi-gen          │ Generate new voucher                   │"
echo "  │  wifi-del          │ Delete voucher                         │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  🛡️ FIREWALL MANAGEMENT                                     │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  wifi-firewall     │ Show rules                             │"
echo "  │  wifi-add-user     │ Add user manually                      │"
echo "  │  wifi-remove-user  │ Remove user                            │"
echo "  │  wifi-clean-users  │ Clean all user rules                   │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  🔄 SERVICE MANAGEMENT                                     │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  wifi-restart      │ Restart all services                   │"
echo "  │  wifi-reload-dns   │ Reload DNS                             │"
echo "  │  wifi-reload-blocks│ Update blocklist                       │"
echo "  │  wifi-reload-whitelist│ Update whitelist                    │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  📊 MONITORING                                             │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  wifi-logs         │ Live logs                              │"
echo "  │  wifi-monitor      │ Live monitoring                        │"
echo "  │  wifi-quick        │ Quick status                           │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  🔧 MAINTENANCE                                            │"
echo "  ├─────────────────────────────────────────────────────────────┤"
echo "  │  wifi-cleanup-db   │ Clean expired vouchers                 │"
echo "  │  wifi-backup       │ Backup database                        │"
echo "  │  wifi-db-size      │ Database size                          │"
echo "  │  wifi-info         │ System info                            │"
echo "  └─────────────────────────────────────────────────────────────┘"
echo ""
echo "💡 Type 'wifi-help' to show this menu again"
echo ""
echo "=================================================================="
