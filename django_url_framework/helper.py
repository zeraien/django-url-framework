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
    
    def url_for(self, controller = None, action = None, named_url  = None, url_params = None, url_args=None, url_kwargs=None):
        from django_url_framework.controller import get_actions, get_controller_name
        
        if controller:
            controller_name = controller
        else:
            controller_name = self.controller._controller_name
            
        Controller = self.controller._site.controllers.get(controller_name, None)
        if Controller is None:
            raise InvalidControllerError(controller_name)
        
        if not named_url:
            if action:
                try:
                    action = action.strip('"\'')
                    action_func = get_actions(Controller,with_prefix=False)[action]
                except KeyError:
                    import traceback
                    traceback.print_exc()
                    raise InvalidActionError(action)
                
                named_url = getattr(action_func,'named_url',None)
                if named_url is None:
                    controller_name = get_controller_name(Controller, with_prefix=False)
                    named_url = '%s_%s' % (controller_name, action)
            else:
                named_url = controller_name
        url = reverse(named_url, args=url_args, kwargs=url_kwargs)
        if url_params is not None:
            return u'%s?%s' % (url, urlencode(url_params))
        return url
