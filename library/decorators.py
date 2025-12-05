from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse


def admin_required(view_func):
    """Decorator to require that the user is authenticated and an admin.

    Admin is considered either `user.is_staff` or membership of group named 'admin'.
    Raises `PermissionDenied` for authenticated non-admins; unauthenticated users
    are redirected by `login_required` behavior.
    """
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        try:
            is_admin = bool(getattr(user, 'is_staff', False) or user.groups.filter(name='admin').exists())
        except Exception:
            is_admin = False

            if not is_admin:
                try:
                    url = reverse('admin_required')
                    return redirect(f"{url}?next={request.path}")
                except Exception:
                    raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped
