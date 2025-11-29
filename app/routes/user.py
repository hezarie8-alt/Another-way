"""
User Routes
مسیرهای مربوط به کاربران
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User
from app.forms import UpdateProfileForm, UpdatePasswordForm, DeleteAccountForm
from app.decorators import login_required
from app.services import StateManager
from app.extensions import db

user_bp = Blueprint('user', __name__)


@user_bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    """نمایش پروفایل کاربر"""
    current_user_id = session['current_user_id']
    user = User.query.get_or_404(user_id)
    can_edit = (current_user_id == user_id)
    
    forms = {
        'update_profile': UpdateProfileForm(obj=user, original_username=user.name) if can_edit else None,
        'update_password': UpdatePasswordForm() if can_edit else None,
        'delete_account': DeleteAccountForm() if can_edit else None
    }
    
    return render_template('profile.html', 
                           user=user, 
                           can_edit=can_edit,
                           update_profile_form=forms['update_profile'],
                           update_password_form=forms['update_password'],
                           delete_account_form=forms['delete_account'])


@user_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """بروزرسانی پروفایل کاربر"""
    user_id = session['current_user_id']
    user = User.query.get_or_404(user_id)
    form = UpdateProfileForm(obj=user, original_username=user.name)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.major = form.major.data
        db.session.commit()
        flash('پروفایل بروزرسانی شد.', 'success')
    
    return redirect(url_for('user.profile', user_id=user_id))


@user_bp.route('/update_password', methods=['POST'])
@login_required
def update_password():
    """تغییر رمز عبور کاربر"""
    user_id = session['current_user_id']
    user = User.query.get_or_404(user_id)
    form = UpdatePasswordForm()
    
    if form.validate_on_submit():
        if check_password_hash(user.password_hash, form.current_password.data):
            user.password_hash = generate_password_hash(form.new_password.data, method='pbkdf2:sha256')
            db.session.commit()
            flash('رمز عبور تغییر کرد.', 'success')
        else:
            flash('رمز عبور فعلی اشتباه است.', 'error')
    
    return redirect(url_for('user.profile', user_id=user_id))


@user_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """حذف حساب کاربری"""
    user_id = session['current_user_id']
    user = User.query.get_or_404(user_id)
    
    StateManager.set_offline(user_id)
    db.session.delete(user)
    db.session.commit()
    session.clear()
    
    flash('حساب کاربری حذف شد.', 'info')
    return redirect(url_for('auth.show_auth_page'))


@user_bp.route('/api/toggle_theme', methods=['POST'])
@login_required
def toggle_theme():
    """تغییر تم (Dark/Light Mode)"""
    user_id = session['current_user_id']
    user = User.query.get_or_404(user_id)
    
    # تغییر تم
    user.theme = 'dark' if user.theme == 'light' else 'light'
    db.session.commit()
    
    return jsonify({'success': True, 'theme': user.theme})