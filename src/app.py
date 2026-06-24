import os
import sys
import time
import sqlite3
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify, redirect, session, render_template

import config
import database
import firewall
from utils import admin_required

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        if request.form.get('password') == config.ADMIN_PASSWORD:
            session['is_admin'] = True
            session['admin_token'] = os.environ.get('ADMIN_SESSION_SECRET')
            session.permanent = True
            return redirect('/admin')
        return render_template('login.html', error="Invalid password / كلمة مرور خاطئة")

    if not session.get('is_admin') or session.get('admin_token') != os.environ.get('ADMIN_SESSION_SECRET'):
        return render_template('login.html', error=None)

    conn = None
    try:
        conn = sqlite3.connect(config.DB_PATH, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT code, duration, status, expiry, used_by_ip, used_by_mac, created_at FROM vouchers ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        def get_count(sql): cursor.execute(sql); res = cursor.fetchone(); return res[0] if res else 0
        total = get_count("SELECT COUNT(*) FROM vouchers")
        active = get_count("SELECT COUNT(*) FROM vouchers WHERE status='active'")
        used = get_count("SELECT COUNT(*) FROM vouchers WHERE status='used'")
        expired = get_count("SELECT COUNT(*) FROM vouchers WHERE status='expired'")
        
        return render_template('dashboard.html', rows=rows, total=total, active=active, used=used, expired=expired)
    except Exception as e:
        logger.error(f"❌ Admin panel error: {e}"); return "Error loading dashboard", 500
    finally:
        if conn: conn.close()

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None); session.pop('admin_token', None)
    return redirect('/admin')

@app.route('/admin/generate', methods=['POST'])
@admin_required
def generate_code():
    duration = request.form.get('duration')
    conn = None
    try:
        conn = sqlite3.connect(config.DB_PATH, timeout=10)
        cursor = conn.cursor()
        code = database.generate_voucher_code(cursor)
        cursor.execute("INSERT INTO vouchers (code, duration, status) VALUES (?, ?, 'active')", (code, duration))
        conn.commit()
        return f'<script>alert("✅ كود جديد: {code}"); window.location.href = "/admin";</script>'
    except Exception as e:
        return f'<script>alert("❌ خطأ: {str(e)}"); window.location.href = "/admin";</script>'
    finally:
        if conn: conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    conn = None
    try:
        if not request.is_json: return jsonify({"status": "fail", "message": "Invalid request"}), 400
        data = request.get_json()
        user_code = data.get('code', '').strip().upper() if data else ''
        if not user_code: return jsonify({"status": "fail", "message": "Please enter code"}), 400

        user_ip = firewall.get_client_ip()
        user_mac = firewall.get_client_mac(user_ip)
        if not user_mac: return jsonify({"status": "fail", "message": "Device physical fingerprint failed"}), 400

        conn = sqlite3.connect(config.DB_PATH, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT duration, status, expiry, used_by_mac FROM vouchers WHERE code=?", (user_code,))
        result = cursor.fetchone()

        if not result: return jsonify({"status": "fail", "message": "Invalid code!"}), 400
        duration, status, expiry, db_mac = result
        now = datetime.now()

        if status == 'expired': return jsonify({"status": "fail", "message": "Code expired!"}), 400

        if status == 'active':
            expiry_str = database.calculate_expiry(duration)
            cursor.execute("UPDATE vouchers SET status='used', expiry=?, used_by_ip=?, used_by_mac=? WHERE code=?", (expiry_str, user_ip, user_mac, user_code))
            conn.commit()
        else:
            if db_mac and db_mac != user_mac: return jsonify({"status": "fail", "message": "Code bound to another device!"}), 403
            if expiry:
                if now > datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S'):
                    cursor.execute("UPDATE vouchers SET status='expired' WHERE code=?", (user_code,))
                    conn.commit()
                    return jsonify({"status": "fail", "message": "Code expired!"}), 400
                cursor.execute("UPDATE vouchers SET used_by_ip=? WHERE code=?", (user_ip, user_code))
                conn.commit()

        conn.close(); conn = None
        if firewall.iptables_add_rule(user_ip, user_mac):
            return jsonify({"status": "success", "result": "success", "success": True, "redirect_url": "http://gstatic.com", "message": "✅ Internet activated!"})
        return jsonify({"status": "error", "message": "Firewall error"}), 500
    except Exception as e:
        logger.error(f"❌ Login error: {e}"); return jsonify({"status": "error", "message": "System error"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/status', methods=['GET'])
def status():
    conn = None
    try:
        conn = sqlite3.connect(config.DB_PATH, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vouchers")
        res = cursor.fetchone()
        return jsonify({"status": "ok", "gateway": config.GATEWAY_IP, "vouchers": res[0] if res else 0, "version": "1.1.0"})
    except Exception: return jsonify({"status": "error"}), 500
    finally:
        if conn: conn.close()

@app.route('/health', methods=['GET'])
def health(): return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

def cleanup_expired_sessions():
    while True:
        conn = None
        try:
            time.sleep(config.CLEANUP_INTERVAL)
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect(config.DB_PATH, timeout=15)
            cursor = conn.cursor()
            cursor.execute("SELECT code, used_by_ip, used_by_mac FROM vouchers WHERE status='used' AND expiry < ?", (now_str,))
            expired_vouchers = cursor.fetchall()

            if expired_vouchers:
                expired_codes = [v[0] for v in expired_vouchers]
                for _, user_ip, user_mac in expired_vouchers:
                    if user_ip and user_mac: firewall.iptables_remove_rule(user_ip, user_mac)
                placeholders = ','.join(['?'] * len(expired_codes))
                cursor.execute(f"UPDATE vouchers SET status='expired' WHERE code IN ({placeholders})", expired_codes)
                conn.commit()
            conn.close(); conn = None
        except Exception as e: logger.error(f"❌ Cleanup error: {e}")
        finally:
            if conn:
                try: conn.close()
                except Exception: pass

@app.route('/admin/reload-whitelist', methods=['GET'])
@admin_required
def reload_whitelist_api():
    """
    Reload the whitelist file and update the firewall rules
    """
    whitelist_path = "/etc/whitelist.txt"
    if not os.path.exists(whitelist_path):
        return jsonify({"status": "error", "message": "File not found"}), 404

    try:
        count = 0
        with open(whitelist_path, "r") as f:
            for line in f:
                ip = line.strip()
                if ip and not ip.startswith("#") and ip != "0.0.0.0":
                    subprocess.run(["iptables", "-D", "AUTH_USERS", "-s", ip, "-j", "ACCEPT"], capture_output=True)
                    subprocess.run(["iptables", "-t", "nat", "-D", "AUTH_NAT", "-s", ip, "-j", "ACCEPT"], capture_output=True)
                    
                    subprocess.run(["iptables", "-A", "AUTH_USERS", "-s", ip, "-j", "ACCEPT"], check=True)
                    subprocess.run(["iptables", "-t", "nat", "-A", "AUTH_NAT", "-s", ip, "-j", "ACCEPT"], check=True)
                    count += 1
                    
        logger.info(f"♻️ Dynamic whitelist reload triggered. {count} device(s) enforced.")
        return jsonify({
            "status": "success", 
            "message": f"تمت إعادة قراءة الملف بنجاح وتفعيل {count} أجهزة في جدار الحماية فوراً!"
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to dynamically reload whitelist: {e}")
        return jsonify({"status": "error", "message": "حدث خطأ أثناء تحديث جدار الحماية"}), 500

@app.route('/admin/delete/<code_id>', methods=['POST'])
@admin_required
def delete_voucher_api(code_id):
    """
    """
    conn = None
    try:
        conn = sqlite3.connect(config.DB_PATH, timeout=10)
        cursor = conn.cursor()
        
        cursor.execute("SELECT used_by_ip, used_by_mac FROM vouchers WHERE code=?", (code_id,))
        res = cursor.fetchone()
        
        if res:
            user_ip, user_mac = res
            if user_ip and user_mac:
                firewall.iptables_remove_rule(user_ip, user_mac)
        
        cursor.execute("DELETE FROM vouchers WHERE code=?", (code_id,))
        conn.commit()
        
        logger.info(f"🗑️ [حذف] قام المسؤول بحذف الكود {code_id} وطرد جهازه بنجاح.")
        return redirect('/admin')
    except Exception as e:
        logger.error(f"❌ خطأ أثناء حذف الكود {code_id}: {e}")
        return "حدث خطأ أثناء الحذف", 500
    finally:
        if conn: conn.close()


@app.route('/admin/add-whitelist', methods=['POST'])
@admin_required
def add_to_whitelist_api():
    """
    Add a new IP address to the whitelist and update firewall rules
    """
    ip = request.form.get('whitelist_ip', '').strip()
    comment = request.form.get('whitelist_comment', '').strip() or "جهاز مستثنى"
    
    if not ip:
        return "الرجاء إدخال عنوان IP صحيح", 400
        
    whitelist_path = "/etc/whitelist.txt"
    try:
        line_to_add = f"{ip} 1; # {comment}\n"
        
        with open(whitelist_path, "a") as f:
            f.write(line_to_add)
            
        subprocess.run(["iptables", "-A", "AUTH_USERS", "-s", ip, "-j", "ACCEPT"], check=True, capture_output=True)
        subprocess.run(["iptables", "-t", "nat", "-A", "AUTH_NAT", "-s", ip, "-j", "ACCEPT"], check=True, capture_output=True)
        
        subprocess.run(["nginx", "-s", "reload"], capture_output=True)
        
        logger.info(f"🟢 [وايت ليست] تم إضافة الجهاز {ip} ({comment}) وتفعيل استثنائه حياً.")
        return redirect('/admin')
    except Exception as e:
        logger.error(f"❌ فشل إضافة الجهاز {ip} للوايت ليست: {e}")
        return f"حدث خطأ أثناء الإضافة: {str(e)}", 500

if __name__ == '__main__':
    database.init_db()
    
    database.load_iptables_whitelist()

    if not config.DEBUG_MODE or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Thread(target=cleanup_expired_sessions, daemon=True).start()
    
    host = '0.0.0.0'
    app.run(host=host, port=5000, debug=config.DEBUG_MODE, threaded=True, use_reloader=config.DEBUG_MODE)

