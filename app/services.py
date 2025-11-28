"""
Business Logic Services
سرویس‌های منطق کسب‌وکار
"""

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_, func, case
from app.extensions import db
from app.models import User, Message

# حافظه موقت برای کاربران آنلاین
ONLINE_USERS_MEMORY = set()


class StateManager:
    """مدیریت وضعیت آنلاین/آفلاین کاربران"""
    
    @staticmethod
    def set_online(user_id):
        """تنظیم کاربر به حالت آنلاین"""
        ONLINE_USERS_MEMORY.add(user_id)

    @staticmethod
    def set_offline(user_id):
        """تنظیم کاربر به حالت آفلاین"""
        if user_id in ONLINE_USERS_MEMORY:
            ONLINE_USERS_MEMORY.remove(user_id)

    @staticmethod
    def is_online(user_id):
        """بررسی آنلاین بودن کاربر"""
        return user_id in ONLINE_USERS_MEMORY


class AuthService:
    """سرویس احراز هویت"""
    
    @staticmethod
    def register_user(name, major, password):
        """ثبت‌نام کاربر جدید"""
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, major=major, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @staticmethod
    def authenticate_user(username, password):
        """احراز هویت کاربر"""
        user = User.query.filter_by(name=username).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None


class ChatService:
    """سرویس چت و پیام‌رسانی"""
    
    @staticmethod
    def get_inbox_conversations(user_id):
        """دریافت لیست مکالمات کاربر"""
        other_user_id = case(
            (Message.sender_id == user_id, Message.receiver_id),
            else_=Message.sender_id
        ).label("other_user_id")

        subquery = db.session.query(
            func.max(Message.id).label("last_message_id")
        ).filter(
            or_(Message.sender_id == user_id, Message.receiver_id == user_id)
        ).group_by(other_user_id).subquery()

        results = db.session.query(
            Message, 
            User, 
            func.sum(
                case(
                    (and_(Message.receiver_id == user_id, Message.read_at.is_(None)), 1), 
                    else_=0
                )
            ).label("unread_count")
        ).join(
            subquery, Message.id == subquery.c.last_message_id
        ).join(
            User, User.id == other_user_id
        ).group_by(Message.id, User.id).order_by(Message.timestamp.desc()).all()

        conversations = []
        for msg, other_user, unread in results:
            conversations.append({
                'other_user_id': other_user.id,
                'other_user_name': other_user.name,
                'last_message_content': msg.content,
                'last_message_timestamp': msg.timestamp,
                'has_unread': unread > 0,
                'is_online': StateManager.is_online(other_user.id)
            })
        return conversations

    @staticmethod
    def get_chat_history(current_user_id, other_user_id, limit=50):
        """دریافت تاریخچه چت بین دو کاربر"""
        # علامت‌گذاری پیام‌ها به عنوان خوانده شده
        Message.query.filter(
            and_(
                Message.sender_id == other_user_id,
                Message.receiver_id == current_user_id,
                Message.read_at.is_(None)
            )
        ).update({Message.read_at: func.now()}, synchronize_session=False)
        db.session.commit()

        # دریافت پیام‌ها
        messages = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == current_user_id)
            )
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        return messages[::-1]

    @staticmethod
    def save_message(sender_id, receiver_id, content):
        """ذخیره پیام جدید"""
        msg = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
        db.session.add(msg)
        db.session.commit()
        return msg