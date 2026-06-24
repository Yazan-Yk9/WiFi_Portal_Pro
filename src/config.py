import os
import secrets

WIFI_IFACE = os.environ.get('WIFI_IFACE', 'wlxfc221c100d54')
WAN_IFACE = os.environ.get('WAN_IFACE', 'wlp12s0b1')
GATEWAY_IP = os.environ.get('GATEWAY_IP', '192.168.50.1')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
DB_PATH = os.environ.get('DB_PATH', '/app/data/portal.db')

VOUCHER_LENGTH = 6
CLEANUP_INTERVAL = 60  # بالثواني
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() in ['true', '1', 't']

FLASK_SECRET_KEY = secrets.token_hex(32)
if 'ADMIN_SESSION_SECRET' not in os.environ:
    os.environ['ADMIN_SESSION_SECRET'] = secrets.token_urlsafe(32)
