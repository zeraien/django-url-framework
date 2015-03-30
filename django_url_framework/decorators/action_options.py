__author__ = 'zeraien'


def name(action_name):
    """custom action name, does not override prefix"""
    def decorator(action_function):
        """custom action name, does not override prefix"""
        action_function.action_name = action_name
        return action_function
    return decorator

def prefix(action_prefix):
    """
    Assign a prefix for the action, applies even if
    you set action_name (template name is based on action_name, sans prefix)

    The prefix will not be taken into account when determining template filenames.
    """
    def decorator(action_function):
        action_function.action_prefix = action_prefix
        return action_function
    return decorator

def template_name(_template_name):
    """custom template filename"""
    def decorator(action_function):
        action_function.template_name = _template_name
        return action_function
    return decorator

def named_url(_named_url):
    """A named url that django can use to call this function. Default is controller_action"""
    def decorator(action_function):
        action_function.named_url = _named_url
        return action_function
    return decorator

def no_ajax_prefix(action_function):
    """Do not prefix template filenames with _ if a request is AJAX."""
    action_function.ignore_ajax = True
    return action_function

def ajax_template_name(_template_name):
    """template filename for ajax responses"""
    def decorator(action_function):
        action_function.ajax_template_name = _template_name
        return action_function
    return decorator

def urlconf(patterns, do_not_autogenerate=True):
    """
    A custom url configuration for this action, just like in Django's urls.py.
    The custom urlconf applies after the urlconf for the controller, unless erase is true.

    Example: `["/user/(?P<user_id>\d+)/"]`

    :param patterns: a url pattern or a list of url patterns
    :param do_not_autogenerate: erase the urlconf that was automatically generated
    """
    if type(patterns) not in (list, tuple):
        patterns = tuple(patterns)

    def decorator(action_function):
        action_function.urlconf = patterns
        action_function.urlconf_erase = do_not_autogenerate
        return action_function
    return decorator

def url_parameters(params):
    """
    A string representing the argument part of the URL for this action, for instance:
    The action 'user' is given the URL `/user/`, by adding `r'(?P<user_id>\d+)'` as the
    url_parameters switch, the URL becomes `/user/(?P<user_id>\d+)`.
    Observe that the parameters do not append a trailing slash automatically, you need to do this yourself.
    The action function has to accept the specified arguments as method parameters.

    Observe that this will have no effect if erase_autogenerated is set to True in the @urlconf decorator.

    :param params: list of url parameters
    """
    def decorator(action_function):
        action_function.url_parameters = params
        return action_function
    return decorator

def disable_filters(action_function):
    """disable before_filter and after_filter for this action"""
    action_function.disable_filters = True
    return action_function
