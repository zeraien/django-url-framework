import inspect
from functools import wraps
from django.http import *
import re
import sys
from django.utils.safestring import SafeUnicode
import warnings
from django_url_framework.helper import ApplicationHelper
from django.utils.translation import ugettext as _
from django.conf.urls import url, include
from django import VERSION
if VERSION[1]<9:
    from django.conf.urls import patterns

from django_url_framework.exceptions import InvalidActionError
from django_url_framework.exceptions import InvalidControllerError

def get_controller_name(controller_class, with_prefix = True):
    controller_name = getattr(controller_class, 'controller_name', None)
    if controller_name is None:
        name_ = [controller_class.__name__[0]]
        prev = ''
        for l in re.sub(r"Controller$",'',controller_class.__name__[1:]):
            if l.isupper() and prev.islower():
                name_.append('_'+l)
            else:
                name_.append(l)
            prev = l
        controller_name = ''.join(name_).lower()

    controller_prefix = getattr(controller_class, 'controller_prefix', None)
    if with_prefix and controller_prefix not in (None, ''):
        controller_name = controller_class.controller_prefix + controller_name
    return controller_name

def autoview_function(site, request, controller_name, controller_class, action_name = 'index', *args, **kwargs):
    error_msg = None
    try:
        # if controller_name in self.controllers:
        # controller_class = self.controllers[controller_name]
        if action_name in get_actions(controller_class):
            helper = ApplicationHelper#self.helpers.get(controller_name, ApplicationHelper)
            kwargs_all = kwargs.copy()
            if hasattr(controller_class, 'consume_urlconf_keyword_arguments'):
                if type(controller_class.consume_urlconf_keyword_arguments) not in (list, tuple):
                    controller_class.consume_urlconf_keyword_arguments = []
                for kwarg in controller_class.consume_urlconf_keyword_arguments:
                    if kwarg in kwargs:
                        del(kwargs[kwarg])
            return controller_class(site, request, helper, url_params=kwargs_all)._call_action(action_name, *args, **kwargs)
        else:
            raise InvalidActionError(action_name)
        # else:
            # raise InvalidControllerError()
    # except InvalidControllerError, e:
        # error_msg = _("No such controller: %(controller_name)s") % {'controller_name' : controller_name}
    except InvalidActionError, e:
        error_msg = _("Action '%(action_name)s' not found in controller '%(controller_name)s'") % {'action_name' : e.message, 'controller_name' : controller_name}
        
    raise Http404(error_msg)


def _get_arg_name_and_default(action_func):
    arg_spec = inspect.getargspec(action_func)
    arguments = arg_spec.args
    has_default = True
    if len(arguments) == 3:
        has_default = arg_spec.defaults and len(arg_spec.defaults) > 0
        return arguments[2], has_default
    return None, has_default

def _patterns(*args):
    if VERSION[1]>=9:
        return list(args)
    else:
        from django.conf.urls import patterns
        return patterns('', *args)

def get_controller_urlconf(controller_class, site=None):
    controller_name = get_controller_name(controller_class)
    actions = get_actions(controller_class)
    urlpatterns = _patterns()
    urlpatterns_with_args = _patterns()
    def wrap_call(_controller_name, _action_name, _action_func):
        """Wrapper for the function called by the url."""
        def wrapper(*args, **kwargs):
            request, args = args[0], args[1:]
            return autoview_function(site, request, _controller_name, controller_class, _action_name, *args, **kwargs)
        return wraps(_action_func)(wrapper)

    for action_name, action_func in actions.items():
        named_url = '%s_%s' % (get_controller_name(controller_class, with_prefix=False), get_action_name(action_func) )
        named_url = getattr(action_func, 'named_url', named_url)
        replace_dict = {'action':action_name.replace("__","/")}
        wrapped_call = wrap_call(controller_name, action_name, action_func)
        urlconf_prefix = getattr(controller_class, 'urlconf_prefix', None)
        action_urlpatterns = _patterns()
        index_action_with_args_urlconf = _patterns()

        if hasattr(action_func, 'urlconf'):
            """Define custom urlconf patterns for this action."""
            for new_urlconf in action_func.urlconf:
                action_urlpatterns += _patterns(url(new_urlconf, view=wrapped_call, name=named_url))
        
        if getattr(action_func, 'urlconf_erase', False) == False:
            """Do not generate default URL patterns if we define 'urlconf_erase' for this action."""
            
            if action_name == 'index':
                # No root URL is generated if we have no index action.

                object_id_arg_name, has_default = _get_arg_name_and_default(action_func)
                if object_id_arg_name is not None:
                    replace_dict['object_id_arg_name'] = object_id_arg_name
                    index_action_with_args_urlconf += _patterns(url(r'^(?P<%(object_id_arg_name)s>[\w-]+)/$' % replace_dict, view=wrapped_call, name=named_url))
                if has_default:
                    action_urlpatterns += _patterns(url(r'^$', view=wrapped_call, name=named_url))

            else:
                if hasattr(action_func, 'url_parameters'):
                    arguments = action_func.url_parameters
                    replace_dict['url_parameters'] = arguments
                    action_urlpatterns += _patterns(url(r'^%(action)s/%(url_parameters)s$' % replace_dict, view=wrapped_call, name=named_url))

                else:
                    object_id_arg_name, has_default = _get_arg_name_and_default(action_func)
                    if object_id_arg_name is not None:
                        replace_dict['object_id_arg_name'] = object_id_arg_name
                        action_urlpatterns += _patterns(url(r'^%(action)s/(?P<%(object_id_arg_name)s>[\w-]+)/$' % replace_dict, view=wrapped_call, name=named_url))
                    if has_default:
                        action_urlpatterns += _patterns(url(r'^%(action)s/$' % replace_dict, view=wrapped_call, name=named_url))

        if urlconf_prefix:
            action_urlpatterns_with_prefix = _patterns()
            for _urlconf in urlconf_prefix:
                action_urlpatterns_with_prefix+=_patterns(url(_urlconf, include(action_urlpatterns)))
            urlpatterns+=action_urlpatterns_with_prefix

            action_urlpatterns_with_args_with_prefix = _patterns()
            for _urlconf in urlconf_prefix:
                action_urlpatterns_with_args_with_prefix+=_patterns(url(_urlconf, include(action_urlpatterns_with_args_with_prefix)))

            urlpatterns_with_args+=action_urlpatterns_with_args_with_prefix
        else:
            urlpatterns+=action_urlpatterns
            urlpatterns_with_args+=index_action_with_args_urlconf

    return urlpatterns+urlpatterns_with_args
CACHED_ACTIONS = {}

def get_action_name(func, with_prefix = False):
    if callable(func):
        func_name = func.func_name
        if not re.match(r'^[_\-A-Z0-9]',func_name[0]):
            if hasattr(func, 'action_name'):
                func_name = func.action_name
            if with_prefix and hasattr(func, 'action_prefix'):
                func_name = func.action_prefix + func_name
            return func_name
    raise InvalidActionError(func.func_name)

def get_actions(controller, with_prefix = True):
    if isinstance(controller, ActionController):
        controller_cache_key = controller.__class__.__name__ + str(with_prefix)
        controller = controller.__class__
    else:
        controller_cache_key = controller.__name__ + str(with_prefix)
        
    if controller_cache_key not in CACHED_ACTIONS:
        actions = {}
        for func_name in dir(controller):
            func = getattr(controller,func_name)
            if not re.match(r'^[_\-A-Z0-9]',func_name[0]) and callable(func):
                if hasattr(func, 'action_name'):
                    func_name = func.action_name
                if with_prefix and hasattr(func, 'action_prefix'):
                    func_name = func.action_prefix + func_name
                actions[func_name] = func
        CACHED_ACTIONS[controller_cache_key] = actions
    return CACHED_ACTIONS[controller_cache_key]

def get_action_wrapper(site, controller_class, action_name):
    """Possible future helper method..."""
    controller_name = get_controller_name(controller_class)
    actions = get_actions(controller_class)
    def wrap_call(controller_name, action_name, action_func):
        """Wrapper for the function called by the url."""
        def wrapper(*args, **kwargs):
            request, args = args[0], args[1:]
            return autoview_function(site, request, controller_name, controller_class, action_name, *args, **kwargs)
        return wraps(action_func)(wrapper)
    
    if action_name in actions:
        wrapped_call = wrap_call(controller_name, action_name, actions[action_name])
        return wrapped_call
    else:
        raise InvalidActionError(action_name)

class ActionController(object):
    """
    Any function that does not start with a _ will be considered an action.

    Returning a dictionary object from an action will render that dictionary in the
    default template for that action. Returning a string will simply print the string.


    ActionControllers can have the following attributes:

        urlconf_prefix
                Set a prefix for all urls in the controller

        consume_urlconf_keyword_arguments
                list - Use together with urlconf_prefix, to avoid passing any of the specified keyword
                arguments to actions
                
        controller_name
                Set the controller's name
    
        controller_prefix
                Set a prefix for the controller's name, applies even if
                you set controller_name (template name is based on controller_name, sans prefix)
    
        no_subdirectories
                Template files should be named ControllerName_ActionName.html, or
                _ControllerName_ActionName.html in the case of ajax requests.
                
                Default: False
                
        template_prefix
                Directory or filename prefix for template files.
                
                Default: controller name sans prefix

        template_extension
                Template file extension, globally replaces extension of templates.
                For example to use jade or another template language.

                Default: html

        no_ajax_prefix
                This controller ignores template file name changes based on the ajax nature of a request.
                If this is False, the template file will be prefixed with _ (underscore) for all ajax requests.
                
                Default: False
            
    Actions can be decorated with a number of features and settings, such as different names, urls and http method access rules.
    See the `django_url_framework.decorators` package.
    
    The prefixes will not be taken into account when determining template filenames.
    
    """
    template_extension = "html"
    template_prefix = None
    no_subdirectories = False
    no_ajax_prefix = False
    controller_prefix = None
    controller_name = None
    consume_urlconf_keyword_arguments = None
    urlconf_prefix = None

    def __init__(self, site, request, helper_class, url_params):
        self._site = site
        self._helper = helper_class(self)
        self._request = request
        self._response = HttpResponse()
        self._action_name = None
        self._action_name_sans_prefix = None
        self._action_func = None
        self._controller_name = get_controller_name(self.__class__)
        self._controller_name_sans_prefix = get_controller_name(self.__class__, with_prefix=False)
        self._flash_cache = None
        self._template_context = {}

        if hasattr(self, 'ignore_ajax'):
            warnings.warn("ActionController.ignore_ajax is deprecated, remove 2017-01-01", DeprecationWarning)
            self._no_ajax_prefix = getattr(self, 'ignore_ajax', False)
        else:
            self._no_ajax_prefix = getattr(self, 'no_ajax_prefix', False)

        self._is_ajax = request.is_ajax()
        self._url_params = url_params

        self._template_extension = getattr(self, 'template_extension', 'html')

        if getattr(self, 'template_prefix') is not None:
            self._template_prefix = getattr(self, 'template_prefix')
        else:
            self._template_prefix = self._controller_name_sans_prefix
            
        if getattr(self, 'no_subdirectories', False):
            self._template_string = "%(controller)s_%(action)s.%(ext)s"
            self._ajax_template_string = "_%(controller)s_%(action)s.%(ext)s"
        else:
            self._template_string = "%(controller)s/%(action)s.%(ext)s"
            self._ajax_template_string = "%(controller)s/_%(action)s.%(ext)s"
        self._actions = get_actions(self, with_prefix = True)
        self._actions_by_name = get_actions(self, with_prefix = False)

    def _get_params(self, all_params=False):
        if self._request.method == "POST":
            return self._request.POST
        else:
            return self._request.REQUEST
    _params = property(_get_params)

    def _call_action(self, action_name, *args, **kwargs):
        if action_name in self._actions:
            action_func = self._actions[action_name]
            action_func = getattr(self, action_func.func_name)
            return self._view_wrapper(action_func,*args, **kwargs)
        else:
            raise InvalidActionError(action_name)

    def _has_action(self, action_name, with_prefix = False):
        return (action_name in get_actions(action_name, with_prefix = with_prefix))
        
    def _get_action_name(self, action_func, with_prefix = True):
        if not re.match(r'^[_\-A-Z0-9]',action_func.func_name[0]) and callable(action_func):
            if hasattr(action_func, 'action_name'):
                func_name = action_func.action_name
            else:
                func_name = action_func.func_name
            if with_prefix and hasattr(action_func, 'action_prefix'):
                func_name = action_func.action_prefix + func_name
            return func_name
        raise InvalidActionError(action_func.func_name)

    def _view_wrapper(self, action_func, *args, **kwargs):
        self._action_name = self._get_action_name(action_func)
        self._action_func = action_func

        if hasattr(action_func, 'ignore_ajax'):
            warnings.warn("action.ignore_ajax is deprecated, remove 2017-01-01", DeprecationWarning)
            self._no_ajax_prefix = self._no_ajax_prefix or getattr(action_func, 'ignore_ajax', False)
        else:
            self._no_ajax_prefix = self._no_ajax_prefix or getattr(action_func, 'no_ajax_prefix', False)

        self._action_name_sans_prefix = self._get_action_name(action_func, with_prefix=False)
        
        if hasattr(action_func,'allowed_methods'):
            if type(action_func.allowed_methods) not in (list, tuple):
                allowed_methods = [action_func.allowed_methods.upper()]
            else:
                allowed_methods = [i.upper() for i in action_func.allowed_methods]
            if self._request.method.upper() not in allowed_methods:
                return HttpResponseNotAllowed(allowed_methods)
                
        send_args = {}
        if hasattr(action_func,'mimetype'):
            send_args['mimetype'] = action_func.mimetype

        try:
            response = self.__wrap_before_filter(action_func, *args, **kwargs)

            if type(response) is dict:
                return self.__wrap_after_filter(self.__wrapped_render, response, **send_args)
            elif type(response) in (str,unicode,SafeUnicode):
                return self.__wrap_after_filter(self.__wrapped_print, response, **send_args)
            else:
                return response

        except Exception, exception:
            response = self._on_exception(request=self._request, exception=exception)
            
            if response is None:
                raise exception, None, sys.exc_info()[-1]
            else:
                if type(response) is dict:
                    return self.__wrapped_render(dictionary=response, template_name=self._get_error_template_path())
                elif type(response) in (str,unicode,SafeUnicode):
                    return self.__wrapped_print(text=response, **send_args)
                else:
                    return response


    def __wrap_before_filter(self, wrapped_func, *args, **kwargs):
        if getattr(self, '_before_filter_runonce', False) == False and getattr(self._action_func,'disable_filters', False) == False:
            self._before_filter_runonce = True

            if self._before_filter.func_code.co_argcount >= 2:
                filter_response = self._before_filter(self._request)
            else:
                filter_response = self._before_filter()
            
            if type(filter_response) is dict:
                self._template_context.update(filter_response)
            elif filter_response is not None:
                return filter_response
        
        if hasattr(self, 'do_not_pass_request'):
            action_response = wrapped_func(*args, **kwargs)
        else:
            action_response = wrapped_func(self._request, *args, **kwargs)
        if type(action_response) is dict:
            self._template_context.update(action_response)
            return self._template_context

        return action_response
        
    def __wrap_after_filter(self, wrapped_func, *args, **kwargs):
        if getattr(self, '_after_filter_runonce', False) == False and getattr(self._action_func,'disable_filters', False) == False:
            self._after_filter_runonce = True
            if self._after_filter.func_code.co_argcount >= 2:
                filter_response = self._after_filter(request=self._request)
            else:
                warnings.warn("_after_filter and _before_filter should always take `request` as second argument.",
                              DeprecationWarning)
                filter_response = self._after_filter()
                
            if type(filter_response) is dict:
                self._template_context.update(filter_response)
            elif filter_response is not None:
                return filter_response
                
        return wrapped_func(*args, **kwargs)

            
    def _before_filter(self, request):
        """If overridden, runs before every action.
        
        Code example:
        {{{
            def _before_filter(self):
                if self._action_name != 'login' and not self._request.user.is_authenticated():
                    return self._redirect(action='login')
                return None
        }}}
        """
        return None
        
    def _after_filter(self, request):
        return None
    def _before_render(self, request = None):
        return None
    def _on_exception(self, request, exception):
        """Can be overriden to handle uncaught exceptions.
        
        If you set the use_action_specific_template attribute on this function,
        each action will need it's own error template, called controller/action__error.html.
        
        The default value for use_action_specific_template is False.
        
        It also accepts template_name and ajax_template_name.
        """
        return None
    
    def _set_cookie(self, *args, **kwargs):
        self._response.set_cookie(*args, **kwargs)
    def _delete_cookie(self, *args, **kwargs):
        self._response.delete_cookie(*args, **kwargs)
    
    def _set_mimetype(self, mimetype, charset = None):
        if mimetype is not None:
            if charset is None:
                charset = self._response._charset
            self._response['content-type'] = "%s; charset=%s" % (mimetype, charset)
    
    def _as_json(self, data, status_code = 200, default=None, *args, **kwargs):
        """Render the returned dictionary as a JSON object. Accepts the json.dumps `default` argument for a custom encoder."""
        import json
        if self._is_ajax and 'mimetype' not in kwargs:
            kwargs['mimetype'] = 'application/json'
        self._template_context = data
        response = self.__wrap_after_filter(json.dumps, self._template_context, default=default)
        if type(response) in (str, unicode, SafeUnicode):
            return self.__wrapped_print(response, status_code=status_code, *args, **kwargs)
        else:
            return response

    def _as_yaml(self, data, default_flow_style = True, status_code = 200, *args, **kwargs):
        """Render the returned dictionary as a YAML object."""
        import yaml
        if self._is_ajax and 'mimetype' not in kwargs:
            kwargs['mimetype'] = 'application/yaml';
        return self._print(yaml.dump(data, default_flow_style=default_flow_style), status_code=status_code, *args, **kwargs)
        
    def __wrapped_print(self, text, mimetype = 'text/plain', charset=None, status_code=200):
        """Print the returned string as plain text."""
        self._before_render()
        self._set_mimetype(mimetype, charset)

        if self._response.status_code == 200:
            self._response.status_code = status_code
            
        self._response.content = text
        return self._response        

    def _print(self, text, mimetype = 'text/plain', charset=None):
        return self.__wrap_after_filter(self.__wrapped_print, text=text, mimetype=mimetype, charset=charset)

    def _get_flash(self):
        if self._flash_cache is None:
            from django_url_framework.flash import FlashManager
            self._flash_cache = FlashManager(self._request)
        return self._flash_cache
    _flash = property(_get_flash)
    
    def _get_error_template_path(self):
        """Return the path to the error template for the current action.
        The error template is called by the action's name, followed by __error (double underscore).
        Example:
        Controller: foo
        Action: list
        Template: foo/list.html
        Error template: foo/list__error.html
        """
        template_name = None
        if self._is_ajax and self._no_ajax_prefix==False and hasattr(self._on_exception,'ajax_template_name'):
            template_name = self._on_exception.ajax_template_name
        elif hasattr(self._on_exception,'template_name'):
            template_name = self._on_exception.template_name
            
        if template_name is None:
            if getattr(self._on_exception, 'use_action_specific_template', False) == False:
                if self._is_ajax and self._no_ajax_prefix==False:
                    template_name = "_error.%(ext)s"
                else:
                    template_name = "error.%(ext)s"
            else:
                template_name_data = {'controller': self._template_prefix,
                                      'action': self._action_name+"__error",
                                      'ext': self._template_extension}
                if self._is_ajax and self._no_ajax_prefix == False:
                    template_name = self._ajax_template_string % template_name_data
                else:
                    template_name = self._template_string % template_name_data
        return template_name
        
    
    def __wrapped_render(self, dictionary = {}, *args, **kwargs):
        """Render the provided dictionary using the default template for the given action.
            The keyword argument 'mimetype' may be used to alter the response type.
        """
        from django.template import loader
        from django.template.context import RequestContext
        
        dictionary.update({
            'request':self._request,
            'controller_name':self._controller_name,
            'controller_actions':self._actions.keys(),
            'action_name':self._action_name,
            'controller_helper':self._helper,
            'flash': self._flash,
        })
        
        mimetype = kwargs.pop('mimetype', None)
        if mimetype:
            self._response['content-type'] = ('Content-Type', mimetype)

        if 'template_name' not in kwargs:
            template_replacement_data = {'controller':self._template_prefix,
                                         'action':self._action_name,
                                         'ext':self._template_extension}

            if self._is_ajax and self._no_ajax_prefix==False:
                if hasattr(self._action_func, 'ajax_template_name'):
                    template_name = self._action_func.ajax_template_name
                else:
                    template_name = self._ajax_template_string % template_replacement_data
            elif hasattr(self._action_func,'template_name'):
                template_name = self._action_func.template_name
            else:
                template_name = self._template_string % template_replacement_data
            kwargs['template_name'] = template_name
            
        if 'context_instance' not in kwargs:
            kwargs['context_instance'] = RequestContext(self._request)

        self._template_context.update(dictionary)
        
        if getattr(self, '_before_render_runonce', False) == False and getattr(self._action_func,'disable_filters', False) == False:
            self._before_render_runonce = True
            before_render_response = self._before_render()
            if type(before_render_response) is dict:
                self._template_context.update(before_render_response)
            elif before_render_response is not None:
                return before_render_response

        # todo used to populate xheaders for debugging purposes
        # obj = getattr(self, '_object',None)
        # if obj is not None:
        #     populate_xheaders(self._request, self._response, obj.__class__, obj.pk)

        self._response.content = loader.render_to_string(dictionary=self._template_context, *args, **kwargs)
        return self._response
    
    _render = __wrapped_render
    
    def __wrapped_redirect(self, to_url, *args, **kwargs):
        if to_url is None:
            to_url = self._helper.url_for(*args, **kwargs)
        return HttpResponseRedirect(to_url)
    def __wrapped_permanent_redirect(self, to_url, *args, **kwargs):
        if to_url is None:
            to_url = self._helper.url_for(*args, **kwargs)
        return HttpResponsePermanentRedirect(to_url)
    
    def _redirect(self, to_url = None, *args, **kwargs):
        return self.__wrap_after_filter(self.__wrapped_redirect, to_url, *args, **kwargs)
    _go = _redirect
    
    def _permanent_redirect(self, to_url, *args, **kwargs):
        return self.__wrap_after_filter(self.__wrapped_permanent_redirect, to_url, *args, **kwargs)
