from django.shortcuts import redirect
from functools import wraps

def login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login') 
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def role_required(allowed_roles):
    """
    Decorator to restrict access to views based on user roles.
    :param allowed_roles: List of roles allowed to access the view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_roles = request.session.get('user_roles', []) 
            if any(role in allowed_roles for role in user_roles):
                return view_func(request, *args, **kwargs)
            return redirect('access_denied') 
        return _wrapped_view
    return decorator