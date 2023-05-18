try:
    from functools import update_wrapper, wraps
except ImportError:
    from django.utils.functional import update_wrapper, wraps  # Python 2.4 fallback.

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect, HttpResponseForbidden
from urllib.parse import quote

from ..lib import is_ajax

def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """
    if not login_url:
        from django.conf import settings
        login_url = settings.LOGIN_URL

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            if test_func(request.user):
                return view_func(self, request, *args, **kwargs)
            path = quote(request.get_full_path())
            tup = login_url, redirect_field_name, path
            if is_ajax(request):
                return HttpResponseForbidden()
            else:
                return HttpResponseRedirect('%s?%s=%s' % tup)
        return _wrapped_view
    return decorator

def must_be_member_of_group(group_name=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    if type(group_name) not in (list, tuple):
        group_name = [group_name]
    actual_decorator = user_passes_test(
        lambda u: (u.is_superuser or u.groups.filter(name__in=group_name).count() > 0),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    return actual_decorator

def superuser_required(function = None, redirect_field_name=REDIRECT_FIELD_NAME):
    actual_decorator = user_passes_test(
        lambda u: u.is_superuser,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def permission_required(perm, login_url=None):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    """
    return user_passes_test(lambda u: u.has_perm(perm), login_url=login_url)

