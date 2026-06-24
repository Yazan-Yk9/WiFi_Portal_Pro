FROM alpine:latest

RUN apk update && apk add --no-cache hostapd dnsmasq iptables iw wireless-tools conntrack-tools nginx curl sqlite python3 py3-pip

RUN python3 -m pip install --no-cache-dir flask --break-system-packages

RUN mkdir -p /app/data \
             /var/www/html \
             /var/log/nginx \
             /var/lib/nginx/logs \
             /etc/hostapd \
             /var/lib/misc

COPY src/ /app/src
COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/hostapd.conf /etc/hostapd/hostapd.conf
COPY config/dnsmasq.conf /etc/dnsmasq.conf
COPY scripts/entrypoint.sh /entrypoint.sh
COPY scripts/aliases.sh /etc/profile.d/aliases.sh
COPY src/templates/index.html /var/www/html/index.html

RUN chmod +x /entrypoint.sh && \
    chown -R nginx:nginx /var/www/html && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /var/lib/nginx

ENV ENV="/etc/profile.d/aliases.sh"

ENTRYPOINT ["/entrypoint.sh"]
