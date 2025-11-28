"""
Extensions Module
تمام extension های Flask در اینجا initialize می‌شوند
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

# Database
db = SQLAlchemy()

# Migration
migrate = Migrate()

# Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)

# SocketIO
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='eventlet'
)