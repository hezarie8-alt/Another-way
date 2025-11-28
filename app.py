"""
Application Entry Point
نقطه ورود برنامه - برای اجرا در Render
"""

import eventlet
eventlet.monkey_patch()

import os
from app import create_app
from app.extensions import db, socketio

# ایجاد Flask app
app = create_app()

if __name__ == '__main__':
    # ایجاد جداول دیتابیس
    with app.app_context():
        db.create_all()
    
    # اجرای سرور
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)