#!/bin/sh

echo "=================================================="
echo "📡 WIFI Portal Pro Starting (Modular Edition)"
echo "=================================================="
echo ""

sysctl -w net.ipv4.ip_forward=1 || echo 1 > /proc/sys/net/ipv4/ip_forward

mkdir -p /var/log/nginx /var/lib/nginx/logs /app/data 2>/dev/null || true
chown -R nginx:nginx /var/log/nginx /var/lib/nginx 2>/dev/null || true

touch /etc/blocklist.txt /etc/whitelist.txt /etc/dnsmasq.adblock.conf 2>/dev/null || true

echo "address=/#/$GATEWAY_IP" > /etc/dnsmasq.portal.conf

[ -f /etc/profile.d/aliases.sh ] && . /etc/profile.d/aliases.sh

ip link set "$WIFI_IFACE" up || echo "⚠️ Could not bring up WIFI_IFACE"
ip addr del "$GATEWAY_IP/24" dev "$WIFI_IFACE" 2>/dev/null || true
ip addr add "$GATEWAY_IP/24" dev "$WIFI_IFACE" || echo "⚠️ Could not assign IP"

iptables -F && iptables -t nat -F && iptables -X && iptables -t nat -X
iptables -P INPUT ACCEPT
iptables -P OUTPUT ACCEPT
iptables -P FORWARD DROP

iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

iptables -A FORWARD -i "$WIFI_IFACE" -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i "$WIFI_IFACE" -p udp --dport 67:68 -j ACCEPT

iptables -N AUTH_USERS
iptables -A FORWARD -i "$WIFI_IFACE" -j AUTH_USERS

iptables -t nat -N AUTH_NAT
iptables -t nat -A PREROUTING -i "$WIFI_IFACE" -j AUTH_NAT

iptables -t nat -A PREROUTING -i "$WIFI_IFACE" -p tcp --dport 80 -j DNAT --to-destination "$GATEWAY_IP:80"

iptables -A FORWARD -i "$WIFI_IFACE" -p tcp --dport 443 -j REJECT --reject-with tcp-reset

iptables -t nat -A POSTROUTING -o "$WAN_IFACE" -j MASQUERADE

echo "🌐 Starting Nginx Web Server..."
nginx &

echo "📡 Starting Hostapd (WIFI Broadcast)..."
hostapd /etc/hostapd/hostapd.conf &

echo "🐍 Starting Captive Portal Core Engine (Flask)..."
cd /app/src
python3 app.py &

if [ -f /etc/profile.d/aliases.sh ]; then
    chmod +x /etc/profile.d/aliases.sh
    . /etc/profile.d/aliases.sh
    echo "✅ Aliases and environment profile loaded successfully."
fi

sleep 3

echo "🔌 Executing Dnsmasq (Core Process)..."
exec dnsmasq --no-daemon --conf-file=/etc/dnsmasq.conf --conf-file=/etc/dnsmasq.portal.conf
