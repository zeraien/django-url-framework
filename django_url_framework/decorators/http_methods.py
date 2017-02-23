__author__ = 'zeraien'


def _append_method(action_function, method_name):
    allowed_methods = getattr(action_function, 'allowed_methods', [])
    allowed_methods.append(method_name)
    action_function.allowed_methods = allowed_methods
    return action_function


def GET(action_function):
    """
    Allow this action to be called with only GET method.
    If multiple decorators are given, it will allow multiple http methods.
    By default all http methods are permitted on all actions.
    """
    return _append_method(action_function, "GET")


def OPTIONS(action_function):
    """
    Allow this action to be called with only OPTIONS method.
    If multiple decorators are given, it will allow multiple http methods.
    By default all http methods are permitted on all actions.
    """
    return _append_method(action_function, "OPTIONS")


def PUT(action_function):
    """
    Allow this action to be called with only PUT method.
    If multiple decorators are given, it will allow multiple http methods.
    By default all http methods are permitted on all actions.
    """
    return _append_method(action_function, "PUT")


def DELETE(action_function):
    """
    Allow this action to be called with only DELETE method.
    If multiple decorators are given, it will allow multiple http methods.
    By default all http methods are permitted on all actions.
    """
    return _append_method(action_function, "DELETE")


def POST(action_function):
    """
    Allow this action to be called with only POST method.
    If multiple decorators are given, it will allow multiple http methods.
    By default all http methods are permitted on all actions.
    """
    return _append_method(action_function, "POST")
