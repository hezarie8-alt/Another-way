import os

class Config:
    """تنظیمات پایه برنامه"""
    
    # Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_prod')
    
    # Database Configuration
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        basedir = os.path.abspath(os.path.dirname(__file__))
        database_url = 'sqlite:///' + os.path.join(basedir, 'app.db')
    else:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # SocketIO Configuration
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URI = "memory://"
    
    # Major Choices
    MAJOR_CHOICES = [
        ('', 'رشته خود را انتخاب کنید'),
        ('مهندسی کامپیوتر', 'مهندسی کامپیوتر'),
        ('علوم کامپیوتر', 'علوم کامپیوتر')
    ]
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'zip', 'rar'}
    
    # VAPID Keys for Web Push (Generate new ones for production!)
    # Generate keys: python -c "from py_vapid import Vapid; v = Vapid(); v.generate_keys(); print('Public:', v.public_key_bytes); print('Private:', v.private_key)"
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
    VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL', 'mailto:admin@example.com')