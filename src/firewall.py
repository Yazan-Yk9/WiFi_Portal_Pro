import subprocess
import logging
from flask import request
import config

logger = logging.getLogger(__name__)

def iptables_add_rule(ip, mac):
    """
    Add iptables rules to allow a specific IP and MAC address to bypass the firewall restrictions."""
    if not ip or not mac or ip in ["0.0.0.0", "127.0.0.1", config.GATEWAY_IP]:
        logger.warning(f"⚠️ حظر محاولة تفعيل غير آمنة للـ IP: {ip} أو MAC: {mac}")
        return False

    try:
        mac_clean = mac.strip().lower()

        subprocess.run(["iptables", "-t", "nat", "-D", "AUTH_NAT", "-s", ip, "-m", "mac", "--mac-source", mac_clean, "-j", "ACCEPT"], capture_output=True)
        subprocess.run(["iptables", "-D", "AUTH_USERS", "-s", ip, "-m", "mac", "--mac-source", mac_clean, "-j", "ACCEPT"], capture_output=True)

        result_nat = subprocess.run(
            ["iptables", "-t", "nat", "-A", "AUTH_NAT", "-s", ip, "-m", "mac", "--mac-source", mac_clean, "-j", "ACCEPT"], 
            capture_output=True, text=True, check=True
        )
        
        result_users = subprocess.run(
            ["iptables", "-A", "AUTH_USERS", "-s", ip, "-m", "mac", "--mac-source", mac_clean, "-j", "ACCEPT"], 
            capture_output=True, text=True, check=True
        )

        logger.info(f"🚀 [ناجح] تم فتح الإنترنت في جدار الحماية للجهاز: IP={ip} | MAC={mac_clean}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ فشل تنفيذ أمر iptables: {e.stderr.strip() if e.stderr else e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطأ حرج أثناء حقن القواعد للجهاز {ip}: {e}")
        return False


def iptables_remove_rule(ip, mac):
    if not ip or not mac: return False
    try:
        subprocess.run(["iptables", "-t", "nat", "-D", "AUTH_NAT", "-s", ip, "-m", "mac", "--mac-source", mac, "-j", "ACCEPT"], check=False, capture_output=True)
        subprocess.run(["iptables", "-D", "AUTH_USERS", "-s", ip, "-m", "mac", "--mac-source", mac, "-j", "ACCEPT"], check=False, capture_output=True)
        subprocess.run(["iptables", "-I", "FORWARD", "-s", ip, "-j", "REJECT", "--reject-with", "tcp-reset"], capture_output=True)
        subprocess.run(["pkill", "-HUP", "dnsmasq"], check=False)
        subprocess.run(["conntrack", "-D", "-s", ip], capture_output=True)
        logger.info(f"🧹 تم عزل الجهاز كلياً: IP={ip} | MAC={mac}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ أثناء حذف قواعد العميل {ip}: {e}")
        return False

def get_client_ip():
    real_ip = request.headers.get('X-Real-IP')
    if real_ip and real_ip.strip() not in ["127.0.0.1", config.GATEWAY_IP]:
        return real_ip.strip()
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        potential_ip = forwarded_for.split(',')[0].strip()
        if potential_ip not in ["127.0.0.1", config.GATEWAY_IP]:
            return potential_ip
    return request.remote_addr

def get_client_mac(ip):
    if not ip or ip in ["127.0.0.1", config.GATEWAY_IP]: return None
    try:
        with open("/proc/net/arp", "r") as f:
            for line in f.readlines()[1:]:
                parts = line.split()
                if len(parts) >= 4 and parts[0] == ip:
                    mac = parts[3]
                    if mac and mac != "00:00:00:00:00:00": return mac.lower()
    except Exception as e:
        logger.error(f"❌ خطأ استخراج الـ MAC: {e}")
    try:
        subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True)
        result = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True)
        if result.returncode == 0 and "lladdr" in result.stdout:
            parts = result.stdout.split()
            idx = parts.index("lladdr")
            return parts[idx + 1].lower()
    except Exception: pass
    return None
