"""
Business Logic Services
سرویس‌های منطق کسب‌وکار
"""

import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_, func, case
from pywebpush import webpush, WebPushException
from app.extensions import db
from app.models import User, Message, PushSubscription
from config import Config

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


class FileService:
    """سرویس مدیریت فایل‌ها"""
    
    @staticmethod
    def allowed_file(filename):
        """بررسی مجاز بودن پسوند فایل"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_file(file):
        """ذخیره فایل و بازگشت اطلاعات آن"""
        if file and FileService.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # ایجاد پوشه uploads در صورت عدم وجود
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            
            # ایجاد نام یونیک برای فایل
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
            
            # ذخیره فایل
            file.save(file_path)
            
            # دریافت اطلاعات فایل
            file_size = os.path.getsize(file_path)
            file_type = filename.rsplit('.', 1)[1].lower()
            
            return {
                'file_path': file_path,
                'file_name': filename,
                'file_type': file_type,
                'file_size': file_size,
                'relative_path': f'uploads/{unique_filename}'
            }
        return None
    
    @staticmethod
    def delete_file(file_path):
        """حذف فایل"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False


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
            or_(Message.sender_id == user_id, Message.receiver_id == user_id),
            Message.is_deleted == False
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
                Message.read_at.is_(None),
                Message.is_deleted == False
            )
        ).update({Message.read_at: func.now()}, synchronize_session=False)
        db.session.commit()

        # دریافت پیام‌ها
        messages = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == current_user_id)
            ),
            Message.is_deleted == False
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        return messages[::-1]

    @staticmethod
    def save_message(sender_id, receiver_id, content, file_info=None):
        """ذخیره پیام جدید"""
        msg = Message(
            sender_id=sender_id, 
            receiver_id=receiver_id, 
            content=content
        )
        
        # اضافه کردن اطلاعات فایل در صورت وجود
        if file_info:
            msg.file_path = file_info.get('file_path')
            msg.file_name = file_info.get('file_name')
            msg.file_type = file_info.get('file_type')
            msg.file_size = file_info.get('file_size')
        
        db.session.add(msg)
        db.session.commit()
        return msg
    
    @staticmethod
    def edit_message(message_id, new_content, current_user_id):
        """ویرایش پیام"""
        msg = Message.query.get(message_id)
        if msg and msg.sender_id == current_user_id and not msg.is_deleted:
            msg.content = new_content
            msg.edited_at = func.now()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def delete_message(message_id, current_user_id):
        """حذف پیام"""
        msg = Message.query.get(message_id)
        if msg and msg.sender_id == current_user_id:
            msg.is_deleted = True
            
            # حذف فایل ضمیمه در صورت وجود
            if msg.file_path:
                FileService.delete_file(msg.file_path)
            
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def search_messages(user_id, query):
        """جستجو در پیام‌های کاربر"""
        messages = Message.query.filter(
            or_(
                Message.sender_id == user_id,
                Message.receiver_id == user_id
            ),
            Message.content.contains(query),
            Message.is_deleted == False
        ).order_by(Message.timestamp.desc()).limit(50).all()
        
        return messages


class NotificationService:
    """سرویس نوتیفیکیشن Web Push"""
    
    @staticmethod
    def save_subscription(user_id, subscription_data):
        """ذخیره اشتراک نوتیفیکیشن"""
        # حذف اشتراک قبلی در صورت وجود
        PushSubscription.query.filter_by(
            user_id=user_id,
            endpoint=subscription_data.get('endpoint')
        ).delete()
        
        # ایجاد اشتراک جدید
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=subscription_data.get('endpoint'),
            p256dh=subscription_data.get('keys', {}).get('p256dh'),
            auth=subscription_data.get('keys', {}).get('auth')
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription
    
    @staticmethod
    def send_notification(user_id, title, body, data=None):
        """ارسال نوتیفیکیشن به کاربر"""
        subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()
        
        notification_data = {
            'title': title,
            'body': body,
            'icon': '/static/images/logo.png',
            'data': data or {}
        }
        
        for subscription in subscriptions:
            try:
                subscription_info = {
                    'endpoint': subscription.endpoint,
                    'keys': {
                        'p256dh': subscription.p256dh,
                        'auth': subscription.auth
                    }
                }
                
                webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(notification_data),
                    vapid_private_key=Config.VAPID_PRIVATE_KEY,
                    vapid_claims={
                        "sub": Config.VAPID_CLAIM_EMAIL
                    }
                )
            except WebPushException as e:
                print(f"Web Push failed: {e}")
                # حذف اشتراک نامعتبر
                if e.response and e.response.status_code in [404, 410]:
                    db.session.delete(subscription)
                    db.session.commit()