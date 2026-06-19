import os
import sqlite3
import subprocess
import threading
import time
import random
import string
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DB_PATH = "/app/data/portal.db"
GATEWAY_IP = os.getenv("GATEWAY_IP", "192.168.50.1")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vouchers 
                      (code TEXT PRIMARY KEY, duration TEXT, status TEXT, expiry TEXT, used_by_ip TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/admin', methods=['GET'])
def admin_panel():
    if request.args.get('pass') != ADMIN_PASSWORD:
        return "غير مصرح لك بالدخول", 403
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vouchers")
    rows = cursor.fetchall()
    conn.close()

    html = '''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>لوحة التحكم</title></head>
    <body style="font-family:Arial; padding:20px; background:#f4f4f4;">
        <h2>📊 إدارة شبكة الواي فاي والأكواد</h2>
        <form action="/admin/generate" method="POST">
            <input type="hidden" name="pass" value="{{admin_pass}}">
            <select name="duration">
                <option value="1h">ساعة واحدة</option>
                <option value="1d">يوم كامل</option>
                <option value="permanent">دائم</option>
            </select>
            <button type="submit">توليد كود جديد</button>
        </form>
        <table border="1" style="width:100%; margin-top:20px; background:white; text-align:center; border-collapse:collapse;">
            <tr style="background:#ddd;"><th>الكود</th><th>المدة</th><th>الحالة</th><th>وقت الانتهاء</th><th>IP الجهاز</th></tr>
            {% for row in rows %}
            <tr><td>{{row[0]}}</td><td>{{row[1]}}</td><td>{{row[2]}}</td><td>{{row[3] or '-'}}</td><td>{{row[4] or '-'}}</td></tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    return render_template_string(html, rows=rows, admin_pass=ADMIN_PASSWORD)

@app.route('/admin/generate', methods=['POST'])
def generate_code():
    if request.form.get('pass') != ADMIN_PASSWORD: return "خطأ", 403
    duration = request.form.get('duration')
    new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vouchers VALUES (?, ?, 'active', NULL, NULL)", (new_code, duration))
    conn.commit()
    conn.close()
    return f"تم إنشاء الكود بنجاح: <b>{new_code}</b> <br><a href='/admin?pass={ADMIN_PASSWORD}'>العودة للوحة التحكم</a>"

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user_code = data.get('code', '').strip().upper()
    user_ip = request.remote_addr

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT duration, status, expiry FROM vouchers WHERE code=?", (user_code,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({"status": "fail", "message": "الكود غير موجود!"})

    duration, status, expiry = result

    if status == 'expired':
        conn.close()
        return jsonify({"status": "fail", "message": "هذا الكود منتهي الصلاحية!"})

    now = datetime.now()
    if status == 'active':
        if duration == "permanent": expiry_time = now + timedelta(days=3650)
        elif duration == "1h": expiry_time = now + timedelta(hours=1)
        elif duration == "1d": expiry_time = now + timedelta(days=1)
        
        expiry_str = expiry_time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("UPDATE vouchers SET status='used', expiry=?, used_by_ip=? WHERE code=?", (expiry_str, user_ip, user_code))
        conn.commit()
    else:
        expiry_time = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S')
        if now > expiry_time:
            cursor.execute("UPDATE vouchers SET status='expired' WHERE code=?", (user_code,))
            conn.commit()
            conn.close()
            return jsonify({"status": "fail", "message": "هذا الكود انتهت صلاحيته للتو!"})

    conn.close()

    subprocess.run(["iptables", "-I", "FORWARD", "-s", user_ip, "-j", "ACCEPT"])
    subprocess.run(["iptables", "-t", "nat", "-I", "PREROUTING", "-s", user_ip, "-j", "ACCEPT"])
    
    return jsonify({"status": "success", "message": "تم تفعيل الإنترنت بنجاح!"})

def cron_cleaner():
    while True:
        time.sleep(60)
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT code, used_by_ip FROM vouchers WHERE status='used' AND expiry < ?", (now_str,))
        expired = cursor.fetchall()
        
        for code, user_ip in expired:
            if user_ip:
                subprocess.run(["iptables", "-D", "FORWARD", "-s", user_ip, "-j", "ACCEPT"])
                subprocess.run(["iptables", "-t", "nat", "-D", "PREROUTING", "-s", user_ip, "-j", "ACCEPT"])
            cursor.execute("UPDATE vouchers SET status='expired' WHERE code=?", (code,))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    threading.Thread(target=cron_cleaner, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)

