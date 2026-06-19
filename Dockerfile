FROM alpine:latest

RUN apk update && \
    apk add --no-cache hostapd dnsmasq iptables iw wireless-tools curl sqlite python3 py3-pip nginx

# تثبيت Flask عبر pip لضمان عدم الاعتماد على مستودعات Alpine المتقلبة
RUN pip3 install --no-cache-dir flask --break-system-packages

WORKDIR /app
COPY hostapd.conf /etc/hostapd/hostapd.conf

COPY aliases.sh /etc/profile.d/aliases.sh

# سكربت الإقلاع الذكي لإدارة جدار الحماية والخدمات
CMD awk '{print "address=/"$1"/0.0.0.0/"}' /etc/blocklist.txt > /etc/dnsmasq.adblock.conf && \
    ip link set $WIFI_IFACE up && \
    ip addr add $GATEWAY_IP/24 dev $WIFI_IFACE && \
    iptables -t nat -A POSTROUTING -o $WAN_IFACE -j MASQUERADE && \
    # قراءة ملف الاستثناء وتمرير الـ PS4 تلقائياً
    if [ -f /etc/whitelist.txt ]; then \
        while read -r ip; do \
            if [ ! -z "$ip" ]; then \
                iptables -I FORWARD -s "$ip" -j ACCEPT && \
                iptables -t nat -I PREROUTING -s "$ip" -j ACCEPT; \
            fi; \
        done < /etc/whitelist.txt; \
    fi && \
    # توجيه بقية الأجهزة غير المسجلة إلى صفحة الكود
    iptables -t nat -A PREROUTING -i $WIFI_IFACE -p tcp --dport 80 -j DNAT --to-destination $GATEWAY_IP:80 && \
    iptables -A FORWARD -i $WIFI_IFACE -j DROP && \
    # تشغيل الخدمات
    python3 /app/app.py & \
    nginx && \
    echo "address=/#/$GATEWAY_IP" > /etc/dnsmasq.portal.conf && \
    dnsmasq --conf-file=/etc/dnsmasq.conf --addn-hosts=/etc/dnsmasq.portal.conf --addn-hosts=/etc/dnsmasq.adblock.conf && \
    hostapd /etc/hostapd/hostapd.conf

