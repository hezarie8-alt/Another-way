from flask import Flask
from config import Config

def create_app(config_class=Config):
    """Factory function برای ایجاد Flask app"""
    
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config_class)
    
    # Initialize Extensions
    from app.extensions import db, migrate, limiter, socketio
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    socketio.init_app(app)
    
    # Register Blueprints
    from app.routes import register_blueprints
    register_blueprints(app)
    
    # Register SocketIO Handlers
    from app.routes.socketio import register_socketio_handlers
    register_socketio_handlers(socketio)
    
    # Context Processor
    @app.context_processor
    def inject_user():
        from flask import session
        from app.models import User
        user_id = session.get('current_user_id')
        if user_id:
            return dict(current_user=User.query.get(user_id), current_user_id=user_id)
        return dict(current_user=None, current_user_id=None)
    
    return app