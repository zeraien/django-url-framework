from functools import wraps

from django.http import HttpResponse


def _action_renderer(renderer, **renderer_kwargs):
    def decorator(function):
        @wraps(function)
        def _wrapped_action(self, *args, **kwargs):
            """Wrapper for the function called by the url."""
            response = function(self, *args, **kwargs)
            if issubclass(response.__class__, HttpResponse):
                return response
            return getattr(self,renderer)(response, **renderer_kwargs)
        return _wrapped_action
    return decorator

def json_action(json_encoder=None):
    """
    Decorator that ensures any data returned from this function is encoded into JSON.
    """
    return _action_renderer(json_encoder=json_encoder, renderer="_as_json")

def yaml_action(default_flow_style=None):

    return _action_renderer(default_flow_style=default_flow_style, renderer="_as_yaml")


def auto(json_encoder=None, yaml_default_flow_style=None):
    """
        Decorator that determines the returned data renderer based on the Accept header.
        Be careful, if used incorrectly this can expose your data to an attacker.

        Example: You request data with Accept:application/json, this means any data returned from your action
        function will be encoded into JSON as is.

        So if you return a dictionary with sensitive data, that normally would be processed inside a server-side
        template, and someone sends Accept:application/json, your function will actually return the dictionary
        that was meant for a server-side template to the client.

        Supported `auto` rendering types are json, yaml, template and plain text.
    """
    return _action_renderer(renderer="_as_auto_response", json_encoder=json_encoder, default_flow_style=yaml_default_flow_style)
