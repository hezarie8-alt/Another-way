"""
Chat Routes
مسیرهای چت و پیام‌رسانی
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app.models import User
from app.services import ChatService, StateManager, FileService, NotificationService
from app.decorators import login_required

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/match')
@login_required
def match():
    """صفحه جستجوی کاربران"""
    current_user_id = session['current_user_id']
    q = request.args.get('q', '')
    
    query = User.query.filter(User.id != current_user_id)
    
    if q:
        users = query.filter((User.major.contains(q)) | (User.name.contains(q))).all()
    else:
        users = query.all()
    
    return render_template('match.html', users=users)


@chat_bp.route('/chat/<int:other_user_id>')
@login_required
def chat(other_user_id):
    """صفحه چت با کاربر خاص"""
    current_user_id = session['current_user_id']
    
    if current_user_id == other_user_id:
        return redirect(url_for('chat.inbox'))
    
    other_user = User.query.get_or_404(other_user_id)
    messages = ChatService.get_chat_history(current_user_id, other_user_id)
    
    return render_template('chat.html', other_user=other_user, messages=messages)


@chat_bp.route('/inbox')
@login_required
def inbox():
    """صفحه صندوق پیام‌ها"""
    current_user_id = session['current_user_id']
    conversations = ChatService.get_inbox_conversations(current_user_id)
    
    return render_template('inbox.html', conversations=conversations, user_id=current_user_id)


@chat_bp.route('/api/user_status/<int:user_id>')
def check_user_online(user_id):
    """API برای بررسی وضعیت آنلاین کاربر"""
    return jsonify({'online': StateManager.is_online(user_id)})


@chat_bp.route('/api/search_messages', methods=['POST'])
@login_required
def search_messages():
    """جستجو در پیام‌ها"""
    current_user_id = session['current_user_id']
    query = request.json.get('query', '')
    
    if len(query) < 2:
        return jsonify({'results': []})
    
    messages = ChatService.search_messages(current_user_id, query)
    
    results = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        receiver = User.query.get(msg.receiver_id)
        
        results.append({
            'id': msg.id,
            'content': msg.content,
            'sender_name': sender.name,
            'receiver_name': receiver.name,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M'),
            'chat_link': url_for('chat.chat', 
                                other_user_id=msg.receiver_id if msg.sender_id == current_user_id else msg.sender_id)
        })
    
    return jsonify({'results': results})


@chat_bp.route('/api/edit_message', methods=['POST'])
@login_required
def edit_message():
    """ویرایش پیام"""
    current_user_id = session['current_user_id']
    message_id = request.json.get('message_id')
    new_content = request.json.get('content')
    
    if ChatService.edit_message(message_id, new_content, current_user_id):
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Cannot edit message'}), 403


@chat_bp.route('/api/delete_message', methods=['POST'])
@login_required
def delete_message():
    """حذف پیام"""
    current_user_id = session['current_user_id']
    message_id = request.json.get('message_id')
    
    if ChatService.delete_message(message_id, current_user_id):
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Cannot delete message'}), 403


@chat_bp.route('/api/subscribe_push', methods=['POST'])
@login_required
def subscribe_push():
    """ذخیره اشتراک نوتیفیکیشن"""
    current_user_id = session['current_user_id']
    subscription_data = request.json
    
    NotificationService.save_subscription(current_user_id, subscription_data)
    
    return jsonify({'success': True})


@chat_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """دانلود فایل آپلود شده"""
    from config import Config
    return send_from_directory(Config.UPLOAD_FOLDER, filename)
# اضافه کنید به انتهای فایل app/routes/chat.py

@chat_bp.route('/api/send_message_with_file', methods=['POST'])
@login_required
def send_message_with_file():
    """ارسال پیام همراه با فایل"""
    current_user_id = session['current_user_id']
    other_user_id = request.form.get('other_user_id', type=int)
    content = request.form.get('content', '')
    file = request.files.get('file')
    
    if not other_user_id:
        return jsonify({'success': False, 'error': 'Invalid user'}), 400
    
    file_info = None
    if file:
        file_info = FileService.save_file(file)
        if not file_info:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    # ذخیره پیام در دیتابیس
    msg = ChatService.save_message(current_user_id, other_user_id, content, file_info)
    
    return jsonify({
        'success': True,
        'message_id': msg.id,
        'file_info': {
            'name': file_info['file_name'],
            'type': file_info['file_type'],
            'size': file_info['file_size'],
            'url': f"/uploads/{file_info['relative_path'].split('/')[-1]}"
        } if file_info else None
    })