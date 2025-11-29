"""
Database Models
مدل‌های پایگاه داده
"""

from app.extensions import db
from sqlalchemy import func, Index

class User(db.Model):
    """مدل کاربر"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    major = db.Column(db.String(100))
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    theme = db.Column(db.String(20), default='light')  # light or dark
    
    def __repr__(self):
        return f'<User {self.name}>'


class Message(db.Model):
    """مدل پیام"""
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=func.now(), index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    edited_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # File attachment fields
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        Index('idx_sender_receiver_timestamp', 'sender_id', 'receiver_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<Message from {self.sender_id} to {self.receiver_id}>'


class PushSubscription(db.Model):
    """مدل اشتراک نوتیفیکیشن"""
    __tablename__ = 'push_subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.String(500), nullable=False)
    p256dh = db.Column(db.String(500), nullable=False)
    auth = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    
    def __repr__(self):
        return f'<PushSubscription for user {self.user_id}>'