from django.utils.http import urlencode

#django <2 compat
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .exceptions import InvalidActionError
from .exceptions import InvalidControllerError

class ApplicationHelper(object):
    """ApplicationHelpers can contain functions useful in a controller. Each controller is assigned a helper.
    Either the global ApplicationHelper, or a class with the same name as the controller such as foo_helper.py,
    and being a subclass of ApplicationHelper."""
    def __init__(self, controller):
        self.controller = controller
    
    def url_for(self, controller = None, action = None, named_url  = None, url_params = None, url_args=None, url_kwargs=None):
        """

        :param controller: a controller name in snake case, without prefix, if you are not redirecting inside the current controller
        :param action: an action name - if a controller is not specified, the action will be in the current controller
        :param named_url: A named URL in django
        :param url_params: The query string params
        :param url_args: the list arguments for this URL, this will be used to build the URL within django's urlresolvers
        :param url_kwargs: the dict arguments for this URL, this will be used to build the URL within django's urlresolvers
        :return:
        """

        if not named_url:
            from .controller import get_actions, get_controller_name

            if controller:
                controllerClassOrInstance = self.controller._site.controllers.get(controller, None)
                if controllerClassOrInstance is None:
                    raise InvalidControllerError(controller)
                controller_name = controller
            else:
                controllerClassOrInstance = self.controller
                controller_name = self.controller._controller_name

            if action:

                try:
                    action = action.strip('"\'')
                    action_func = get_actions(controllerClassOrInstance,with_prefix=False)[action]
                except KeyError:
                    raise InvalidActionError(action)
                
                named_url = getattr(action_func,'named_url',None)
                if named_url is None:
                    controller_name = get_controller_name(controllerClassOrInstance, with_prefix=False)
                    named_url = '%s_%s' % (controller_name, action)
            else:
                named_url = "%s_index" % controller_name

        url = reverse(named_url, args=url_args, kwargs=url_kwargs)
        if url_params is not None:
            return '%s?%s' % (url, urlencode(url_params))
        return url
