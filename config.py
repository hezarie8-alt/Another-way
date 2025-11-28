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