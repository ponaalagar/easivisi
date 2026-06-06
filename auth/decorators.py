"""
EasiVisi - Authentication Decorators
Custom decorators for access control and permissions
"""
from functools import wraps
from flask import abort, redirect, url_for, request, jsonify
from flask_login import current_user


def login_required(f):
    """
    Decorator to require user authentication.
    
    Redirects to login page if not authenticated.
    Returns 401 JSON for API requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    """
    Decorator to require specific permission.
    
    Args:
        permission: Required permission name
    
    Usage:
        @permission_required('delete')
        def delete_dataset():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.has_permission(permission):
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Permission denied'}), 403
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to require admin role.
    
    Usage:
        @admin_required
        def admin_panel():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def anonymous_required(f):
    """
    Decorator to require user NOT to be authenticated.
    Redirects to index if already logged in.
    
    Usage:
        @anonymous_required
        def login():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
