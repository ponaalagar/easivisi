"""
EasiVisi - Authentication Routes
User registration, login, logout, and profile management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user
from datetime import datetime

from database import db
from models.user import User
from auth.decorators import login_required, anonymous_required

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    """User registration page and handler."""
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')
            full_name = request.form.get('full_name', '').strip()
            
            # Validation
            errors = []
            
            if not username or len(username) < 3:
                errors.append('Username must be at least 3 characters')
            
            if not email or '@' not in email:
                errors.append('Valid email is required')
            
            if not password or len(password) < 8:
                errors.append('Password must be at least 8 characters')
            
            if password != confirm:
                errors.append('Passwords do not match')
            
            # Check if username exists
            if User.query.filter_by(username=username).first():
                errors.append('Username already taken')
            
            # Check if email exists
            if User.query.filter_by(email=email).first():
                errors.append('Email already registered')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('auth/register.html')
            
            # Create new user
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                role='user',  # Default role
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    """User login page and handler."""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password')
            remember = request.form.get('remember') == 'on'
            
            # Find user
            user = User.query.filter_by(username=username).first()
            
            if not user or not user.check_password(password):
                flash('Invalid username or password', 'error')
                return render_template('auth/login.html')
            
            if not user.is_active:
                flash('Your account has been deactivated', 'error')
                return render_template('auth/login.html')
            
            # Log user in
            login_user(user, remember=remember)
            user.update_last_login()
            
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout handler."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    try:
        full_name = request.form.get('full_name', '').strip()
        bio = request.form.get('bio', '').strip()
        
        current_user.full_name = full_name
        current_user.bio = bio
        current_user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update profile: {str(e)}', 'error')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/password/change', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('auth.profile'))
        
        # Validate new password
        if len(new_password) < 8:
            flash('New password must be at least 8 characters', 'error')
            return redirect(url_for('auth.profile'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('auth.profile'))
        
        # Update password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Password changed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to change password: {str(e)}', 'error')
    
    return redirect(url_for('auth.profile'))


# API Routes for username/email availability check
@auth_bp.route('/api/check-username/<username>')
def check_username(username):
    """Check if username is available (AJAX endpoint)."""
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({'available': not exists})


@auth_bp.route('/api/check-email/<email>')
def check_email(email):
    """Check if email is available (AJAX endpoint)."""
    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({'available': not exists})
