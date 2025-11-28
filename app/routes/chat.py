"""
Chat Routes
مسیرهای چت و پیام‌رسانی
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models import User
from app.services import ChatService, StateManager
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