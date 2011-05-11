from django.utils.http import urlencode
from django.core.urlresolvers import reverse
from django_url_framework.exceptions import InvalidActionError
from django_url_framework.exceptions import InvalidControllerError

class ApplicationHelper(object):
    """ApplicationHelpers can contain functions useful in a controller. Each controller is assigned a helper.
    Either the global ApplicationHelper, or a class with the same name as the controller such as foo_helper.py,
    and being a subclass of ApplicationHelper."""
    def __init__(self, controller):
        self.controller = controller
    
    def url_for(self, *args, **kwargs):
        from django_url_framework.controller import get_actions, get_controller_name
        
        controller_name = kwargs.pop('controller', self.controller._controller_name)
        Controller = self.controller._site.controllers.get(controller_name, None)
        if Controller is None:
            raise InvalidControllerError(controller_name)
            
        if 'named_url' in kwargs:
            named_url = kwargs.pop('named_url')
        elif 'action' in kwargs:
            action_name = kwargs.pop('action')
            try:
                action_func = get_actions(Controller,with_prefix=False)[action_name]
            except KeyError:
                raise InvalidActionError(action_name)
                
            named_url = getattr(action_func,'named_url',None)
            if named_url is None:
                controller_name = get_controller_name(Controller, with_prefix=False)
                named_url = '%s_%s' % (controller_name, action_name)
        else:
            named_url = controller_name
        url_params = kwargs.pop('url_params',None)
        url = reverse(named_url, args=args, kwargs=kwargs)
        if url_params is not None:
            return u'%s?%s' % (url, urlencode(url_params))
        return url
