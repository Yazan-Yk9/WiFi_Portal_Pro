import os
import logging
from functools import wraps
from flask import request, redirect, jsonify, session

logger = logging.getLogger(__name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin') or session.get('admin_token') != os.environ.get('ADMIN_SESSION_SECRET'):
            logger.warning(f"🔒 محاولة دخول غير مصرحة من: {request.remote_addr}")
            if request.method == 'GET':
                return redirect('/admin')
            return jsonify({"error": "Unauthorized / غير مصرح"}), 403
        return f(*args, **kwargs)
    return decorated_function
