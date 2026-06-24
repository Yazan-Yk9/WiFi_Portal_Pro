import os
import sqlite3
import random
import string
import logging
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)

def init_db():
    try:
        if os.path.dirname(config.DB_PATH):
            os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(config.DB_PATH, timeout=10)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS vouchers
                          (code TEXT PRIMARY KEY, duration TEXT, status TEXT, expiry TEXT,
                           used_by_ip TEXT, used_by_mac TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status_expiry ON vouchers(status, expiry)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_used_by_ip ON vouchers(used_by_ip)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_used_by_mac ON vouchers(used_by_mac)')
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database error: {e}"); raise

def generate_voucher_code(cursor=None):
    charset = ''.join([c for c in string.ascii_uppercase + string.digits if c not in ['O', '0', 'I', '1']])
    local_conn = None
    if cursor is None:
        local_conn = sqlite3.connect(config.DB_PATH, timeout=10)
        cursor = local_conn.cursor()
    try:
        for _ in range(10):
            code = ''.join(random.choices(charset, k=config.VOUCHER_LENGTH))
            cursor.execute("SELECT 1 FROM vouchers WHERE code=?", (code,))
            if not cursor.fetchone(): return code
        raise Exception("Failed to generate unique code")
    finally:
        if local_conn: local_conn.close()

def calculate_expiry(duration):
    now = datetime.now()
    durations = {
        "1h": timedelta(hours=1), "2h": timedelta(hours=2), "4h": timedelta(hours=4),
        "8h": timedelta(hours=8), "1d": timedelta(days=1), "2d": timedelta(days=2),
        "1w": timedelta(days=7), "1m": timedelta(days=30), "permanent": timedelta(days=3650)
    }
    expiry_datetime = now + durations.get(duration, timedelta(hours=1))
    return expiry_datetime.strftime('%Y-%m-%d %H:%M:%S')

def load_iptables_whitelist():
    """
    Load the whitelist into iptables rules
    """
    whitelist_path = "/etc/whitelist.txt"
    if os.path.exists(whitelist_path) and os.path.getsize(whitelist_path) > 0:
        try:
            with open(whitelist_path, "r") as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith("#") and ip != "0.0.0.0":
                        subprocess.run(["iptables", "-A", "AUTH_USERS", "-s", ip, "-j", "ACCEPT"], capture_output=True)
                        subprocess.run(["iptables", "-t", "nat", "-A", "AUTH_NAT", "-s", ip, "-j", "ACCEPT"], capture_output=True)
            logger.info("✅ Whitelist loaded successfully / تم تحميل القائمة البيضاء بنجاح")
        except Exception as e:
            logger.error(f"❌ Error loading whitelist: {e}")
