"""
Routes Package
ثبت تمام Blueprint ها
"""

def register_blueprints(app):
    """ثبت تمام blueprints در app"""
    
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.chat import chat_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(chat_bp)