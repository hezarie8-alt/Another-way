"""
WTForms
فرم‌های برنامه
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import User
from config import Config


class RegistrationForm(FlaskForm):
    """فرم ثبت‌نام"""
    name = StringField('نام کاربری', validators=[DataRequired(), Length(min=4, max=100)])
    major = SelectField('رشته تحصیلی', choices=Config.MAJOR_CHOICES, validators=[DataRequired()])
    password = PasswordField('رمز عبور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تکرار رمز عبور', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('ثبت‌نام')
    
    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('این نام کاربری قبلاً استفاده شده است.')


class LoginForm(FlaskForm):
    """فرم ورود"""
    username = StringField('نام کاربری', validators=[DataRequired()])
    password = PasswordField('رمز عبور', validators=[DataRequired()])
    submit = SubmitField('ورود')


class UpdateProfileForm(FlaskForm):
    """فرم بروزرسانی پروفایل"""
    name = StringField('نام کاربری', validators=[DataRequired(), Length(min=4, max=100)])
    major = SelectField('رشته تحصیلی', choices=Config.MAJOR_CHOICES)
    submit = SubmitField('بروزرسانی پروفایل')
    
    def __init__(self, original_username, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
    
    def validate_name(self, field):
        if field.data != self.original_username:
            if User.query.filter_by(name=field.data).first():
                raise ValidationError('نام کاربری جدید تکراری است.')


class UpdatePasswordForm(FlaskForm):
    """فرم تغییر رمز عبور"""
    current_password = PasswordField('رمز عبور فعلی', validators=[DataRequired()])
    new_password = PasswordField('رمز عبور جدید', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('تکرار رمز عبور جدید', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('تغییر رمز عبور')


class DeleteAccountForm(FlaskForm):
    """فرم حذف حساب کاربری"""
    submit = SubmitField('حذف حساب کاربری')