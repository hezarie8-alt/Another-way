"""
SocketIO Event Handlers
هندلرهای رویدادهای SocketIO
"""

from flask import session, request
from flask_socketio import emit, join_room
from app.models import User
from app.services import ChatService, StateManager, FileService, NotificationService


def register_socketio_handlers(socketio):
    """ثبت تمام event handler های SocketIO"""
    
    @socketio.on('connect')
    def handle_connect():
        """هنگام اتصال کاربر"""
        current_user_id = session.get('current_user_id')
        if current_user_id:
            StateManager.set_online(current_user_id)
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """هنگام قطع اتصال کاربر"""
        current_user_id = session.get('current_user_id')
        if current_user_id:
            StateManager.set_offline(current_user_id)
    
    @socketio.on('join_chat')
    def handle_join_chat(data):
        """ورود به اتاق چت"""
        current_user_id = session.get('current_user_id')
        if not current_user_id:
            return
        
        other_user_id = data['other_user_id']
        room_id = f"chat-{min(current_user_id, other_user_id)}-{max(current_user_id, other_user_id)}"
        join_room(room_id)
        
        user = User.query.get(current_user_id)
        emit('status_message', 
             {'msg': f"{user.name} متصل شد.", 'type': 'join'}, 
             room=room_id, 
             include_self=False)
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """ارسال پیام"""
        current_user_id = session.get('current_user_id')
        if not current_user_id:
            return
        
        other_user_id = data.get('other_user_id')
        content = data.get('content')
        file_info = data.get('file_info')
        
        if not other_user_id or not content:
            return
        
        msg = ChatService.save_message(current_user_id, other_user_id, content, file_info)
        room_id = f"chat-{min(current_user_id, other_user_id)}-{max(current_user_id, other_user_id)}"
        
        user = User.query.get(current_user_id)
        
        message_data = {
            'sender_name': user.name,
            'content': content,
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'sender_id': current_user_id,
            'message_id': msg.id
        }
        
        # اضافه کردن اطلاعات فایل
        if msg.file_path:
            message_data['file'] = {
                'name': msg.file_name,
                'type': msg.file_type,
                'size': msg.file_size,
                'url': f'/uploads/{msg.file_path.split("/")[-1]}'
            }
        
        emit('new_message', message_data, room=room_id, include_self=False)
        
        # ارسال نوتیفیکیشن به گیرنده
        if not StateManager.is_online(other_user_id):
            NotificationService.send_notification(
                other_user_id,
                f'پیام جدید از {user.name}',
                content[:50] + ('...' if len(content) > 50 else ''),
                {'url': f'/chat/{current_user_id}'}
            )
    
    @socketio.on('edit_message')
    def handle_edit_message(data):
        """ویرایش پیام"""
        current_user_id = session.get('current_user_id')
        if not current_user_id:
            return
        
        message_id = data.get('message_id')
        new_content = data.get('content')
        other_user_id = data.get('other_user_id')
        
        if ChatService.edit_message(message_id, new_content, current_user_id):
            room_id = f"chat-{min(current_user_id, other_user_id)}-{max(current_user_id, other_user_id)}"
            emit('message_edited', {
                'message_id': message_id,
                'new_content': new_content
            }, room=room_id)
    
    @socketio.on('delete_message')
    def handle_delete_message(data):
        """حذف پیام"""
        current_user_id = session.get('current_user_id')
        if not current_user_id:
            return
        
        message_id = data.get('message_id')
        other_user_id = data.get('other_user_id')
        
        if ChatService.delete_message(message_id, current_user_id):
            room_id = f"chat-{min(current_user_id, other_user_id)}-{max(current_user_id, other_user_id)}"
            emit('message_deleted', {
                'message_id': message_id
            }, room=room_id)
    
    @socketio.on('typing')
    def handle_typing(data):
        """در حال تایپ"""
        current_user_id = session.get('current_user_id')
        if current_user_id and data.get('room'):
            emit('typing', 
                 {'user_id': current_user_id}, 
                 room=data['room'], 
                 include_self=False)
    
    @socketio.on('stop_typing')
    def handle_stop_typing(data):
        """توقف تایپ"""
        current_user_id = session.get('current_user_id')
        if current_user_id and data.get('room'):
            emit('stop_typing', 
                 {'user_id': current_user_id}, 
                 room=data['room'], 
                 include_self=False)