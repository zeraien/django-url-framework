from __future__ import annotations

from types import FunctionType

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import path

import django_url_framework #for type hinting
import inspect
from functools import wraps
from json.encoder import JSONEncoder
from typing import Union, Tuple, Iterable, Optional

from django.http import *
import re
import sys

import warnings

from .renderers import JSONRenderer, YAMLRenderer, TextRenderer, TemplateRenderer, Renderer, RedirectRenderer
from .helper import ApplicationHelper
from django.conf.urls import url, include
from django import VERSION
if VERSION[:2]<(1,9):
    from django.conf.urls import patterns

from .exceptions import ConfigurationError
from .exceptions import MethodNotAllowed
from .exceptions import InvalidActionError

def get_controller_name(controller_class:'ActionController.__class__', with_prefix:bool = True) -> str:
    if isinstance(controller_class, ActionController):
        controller_class = controller_class.__class__

    controller_name = getattr(controller_class, 'controller_name', None)
    use_inflection_lib = getattr(controller_class,"use_inflection_library",False) #todo defaults to True in 2021
    if controller_name is None:
        if use_inflection_lib:
            import inflection
            controller_name = re.sub(r"_controller$", "", inflection.underscore(controller_class.__name__))
        else:
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

def autoview_function(site:'django_url_framework.site.Site', request, controller_name:str, controller_class:'ActionController.__class__', action_name:str = 'index', *args, **kwargs) -> HttpResponse:
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
            return controller_class(site=site, request=request, helper_class=helper, url_params=kwargs_all)._call_action(action_name, *args, **kwargs)
        else:
            raise InvalidActionError(action_name)
        # else:
            # raise InvalidControllerError()
    # except InvalidControllerError, e:
        # error_msg = _("No such controller: %(controller_name)s") % {'controller_name' : controller_name}
    except InvalidActionError as e:
        error_msg = "Action '%(action_name)s' not found in controller '%(controller_name)s'" % {'action_name' : e, 'controller_name' : controller_name}

    raise Http404(error_msg)

def _is_action_func(action_func):
    """
    check that the function does not start with underscore and has request as it's second parameter

    :param action_func:
    :return:
    """
    # if the passed function was wrapped with a decorator, let's make sure to get the actual function
    while hasattr(action_func,"__wrapped__"):
        action_func = action_func.__wrapped__
    if not callable(action_func) or not isinstance(action_func, FunctionType):
        return False

    func_name = action_func.__name__
    if re.match(r'^[_\-A-Z0-9]',func_name[0]):
        return False

    arg_spec = inspect.getfullargspec(action_func)
    arguments = arg_spec.args
    if len(arguments)>1 and arguments[1]=="request":
        return True
    return False

def _get_urlconf_param_type(datatype:type):
    if datatype is None or datatype not in (int,str):
        p = "slug"
    else:
        p = datatype.__name__
    return p

def _get_arg_name_and_default(action_func)->Tuple[Optional[str],bool,Optional[type]]:
    """
    This extracts the 3rd argument of the provided function and checks if it has a default value.
    `def action(self, request, returns_this_name=?):`

    :param action_func: the function to extract from
    :return: tuple with the argument name and a boolean of whether it has a default value or not, as well as the datatype inferred from the annotation or `[\w-]` if the annotation is missing
    """

    # if the passed function was wrapped with a decorator, let's make sure to get the actual function
    while hasattr(action_func,"__wrapped__"):
        action_func = action_func.__wrapped__

    arg_spec = inspect.getfullargspec(action_func)
    arguments = arg_spec.args
    if len(arguments) == 3:
        has_default = arg_spec.defaults and len(arg_spec.defaults) > 0
        arg_name = arguments[2]
        if arg_name in arg_spec.annotations:
            datatype = arg_spec.annotations[arg_name]
        else:
            datatype = None
        return arg_name, has_default, datatype
    return None, True, None

def url_patterns(*args):
    if VERSION[:2]>=(1,9):
        return list(args)
    else:
        return patterns('', *args)

def get_controller_urlconf(controller_class:'ActionController.__class__', site=None):
    controller_name = get_controller_name(controller_class)
    actions = get_actions(controller_class)
    urlpatterns = url_patterns()
    urlpatterns_with_args = url_patterns()
    def wrap_call(_controller_name, _action_name, _action_func):
        """Wrapper for the function called by the url."""
        def wrapper(*args, **kwargs):
            request, args = args[0], args[1:]
            return autoview_function(site=site,
                                     request=request,
                                     controller_name=_controller_name,
                                     controller_class=controller_class,
                                     action_name=_action_name, *args, **kwargs)
        return wraps(_action_func)(wrapper)

    for action_name, action_func in list(actions.items()):
        named_url = '%s_%s' % (get_controller_name(controller_class, with_prefix=False), get_action_name(action_func) )
        named_url = getattr(action_func, 'named_url', named_url)
        replace_dict = {'action':action_name.replace("__","/")}
        wrapped_call = wrap_call(controller_name, action_name, action_func)
        urlconf_prefix = getattr(controller_class, 'urlconf_prefix', None)
        action_urlpatterns = url_patterns()
        index_action_with_args_urlconf = url_patterns()

        if hasattr(action_func, 'urlconf'):
            """Define custom urlconf patterns for this action."""
            for new_urlconf in action_func.urlconf:
                action_urlpatterns += url_patterns(url(new_urlconf, view=wrapped_call, name=named_url))

        if not getattr(action_func, 'urlconf_erase', False):
            """Do not generate default URL patterns if we define 'urlconf_erase' for this action."""

            if action_name == 'index':
                # No root URL is generated if we have no index action.

                object_id_arg_name, has_default, datatype = _get_arg_name_and_default(action_func)
                if object_id_arg_name is not None:
                    replace_dict['object_id_arg_name'] = object_id_arg_name
                    replace_dict['type'] = _get_urlconf_param_type(datatype)
                    index_action_with_args_urlconf += url_patterns(path("<%(type)s:%(object_id_arg_name)s>/" % replace_dict, view=wrapped_call, name=named_url))
                if has_default:
                    action_urlpatterns += url_patterns(url(r'^$', view=wrapped_call, name=named_url))

            else:
                if hasattr(action_func, 'url_parameters'):
                    arguments = action_func.url_parameters
                    replace_dict['url_parameters'] = arguments
                    action_urlpatterns += url_patterns(url(r'^%(action)s/%(url_parameters)s$' % replace_dict, view=wrapped_call, name=named_url))

                else:
                    object_id_arg_name, has_default, datatype = _get_arg_name_and_default(action_func)
                    if object_id_arg_name is not None:
                        replace_dict['object_id_arg_name'] = object_id_arg_name
                        replace_dict['type'] = _get_urlconf_param_type(datatype)
                        action_urlpatterns += url_patterns(path('%(action)s/<%(type)s:%(object_id_arg_name)s>/' % replace_dict, view=wrapped_call, name=named_url))
                    if has_default:
                        action_urlpatterns += url_patterns(path('%(action)s/' % replace_dict, view=wrapped_call, name=named_url))

        if urlconf_prefix:
            action_urlpatterns_with_prefix = url_patterns()
            for _urlconf in urlconf_prefix:
                action_urlpatterns_with_prefix+=url_patterns(url(_urlconf, include(action_urlpatterns)))
            urlpatterns+=action_urlpatterns_with_prefix

            action_urlpatterns_with_args_with_prefix = url_patterns()
            for _urlconf in urlconf_prefix:
                action_urlpatterns_with_args_with_prefix+=url_patterns(url(_urlconf, include(action_urlpatterns_with_args_with_prefix)))

            urlpatterns_with_args+=action_urlpatterns_with_args_with_prefix
        else:
            urlpatterns+=action_urlpatterns
            urlpatterns_with_args+=index_action_with_args_urlconf

    return urlpatterns+urlpatterns_with_args
CACHED_ACTIONS = {}

def get_action_name(func, with_prefix = False):
    if callable(func):
        func_name = func.__name__
        if not re.match(r'^[_\-A-Z0-9]',func_name[0]):
            if hasattr(func, 'action_name'):
                func_name = func.action_name
            if with_prefix and hasattr(func, 'action_prefix'):
                func_name = func.action_prefix + func_name
            return func_name
    raise InvalidActionError(func.__name__)

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
            if _is_action_func(action_func=func):
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

default_charset = 'utf8'

class ActionController(object):
    """
    Any function that does not start with a _ will be considered an action.

    Returning a dictionary object from an action will render that dictionary in the
    default template for that action. Returning a string will simply print the string.


    ActionControllers can have the following attributes:

        urlconf_prefix:list
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

        json_default_encoder
                Allows you to specify a custom JSON encoder class for all json encoding. Default is `DjangoJSONEncoder`

        use_inflection_library
                Use this to convert controller class names using a new method, with the `inflection` library.
                This will become the default after 2021. You can also set it as a global default in Site.autodiscover

    Actions can be decorated with a number of features and settings, such as different names, urls and http method access rules.
    See the `django_url_framework.decorators` package.
    
    The prefixes will not be taken into account when determining template filenames.
    
    """
    template_extension:str = "html"
    template_prefix = None
    no_subdirectories = False
    no_ajax_prefix = False
    controller_prefix = None
    controller_name = None
    consume_urlconf_keyword_arguments:Iterable[str] = None
    urlconf_prefix:list = None
    json_default_encoder:JSONEncoder = DjangoJSONEncoder
    yaml_default_flow_style:bool = True
    use_inflection_library:Optional[bool] = None
    default_renderer = TemplateRenderer

    def __init__(self, site, request, helper_class, url_params):
        self._site = site
        if helper_class is None: helper_class = ApplicationHelper
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

        if not issubclass(ActionController.default_renderer, Renderer):
            raise ConfigurationError("Invalid `default_renderer`, must be subclass of `Renderer`.")

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
        """
        :param action_name:
        :param args:
        :param kwargs: the kwargs parsed from the URL
        :return:
        """
        if action_name in self._actions:
            action_func = self._actions[action_name]
            action_func = getattr(self, action_func.__name__)
            return self._view_wrapper(action_func,*args, **kwargs)
        else:
            raise InvalidActionError(action_name)

    def _has_action(self, action_name, with_prefix = False):
        return (action_name in get_actions(action_name, with_prefix = with_prefix))
        
    def _get_action_name(self, action_func, with_prefix = True):
        if not re.match(r'^[_\-A-Z0-9]',action_func.__name__[0]) and callable(action_func):
            if hasattr(action_func, 'action_name'):
                func_name = action_func.action_name
            else:
                func_name = action_func.__name__
            if with_prefix and hasattr(action_func, 'action_prefix'):
                func_name = action_func.action_prefix + func_name
            return func_name
        raise InvalidActionError(action_func.__name__)

    def _get_renderer_for_request(self, data, **kwargs):
        accept_types = self._request.headers.get("Accept")
        content_type = None
        if accept_types:
            if isinstance(accept_types, (list,tuple)):
                if len(accept_types)>0:
                    content_type = accept_types[0]
            else:
                split_types = list(map(lambda x:x.strip(), accept_types.split(",")))
                if len(split_types)>0:
                    content_type = split_types[0]

        _renderers_for_contenttypes = {
            'text/html': TemplateRenderer,
            'text/plain': TextRenderer,
            "application/json":JSONRenderer,
            "application/yaml":YAMLRenderer
        }

        renderer_klass = _renderers_for_contenttypes.get(content_type)

        if not renderer_klass:
            renderer_klass = TextRenderer

        return self._instantiate_renderer(
            renderer_klass=renderer_klass,
            data=data,
            **kwargs)

    def _instantiate_renderer(self, renderer_klass, data, **kwargs):

        _default_params = {
            YAMLRenderer: {'default_flow_style': self.yaml_default_flow_style},
            JSONRenderer: {'json_default_encoder':self.json_default_encoder},
        }
        if renderer_klass in _default_params:
            kwargs.update(_default_params[renderer_klass])
        return renderer_klass(data=data, **kwargs)


    def _check_http_method_access(self, action_func):
        """
        return a list of allowed http methods, if the request.method is not one of them.
        If we're allowed, return None.[
        :param action_func:
        :return:
        """
        allowed_methods = getattr(action_func, "allowed_methods",
                                  getattr(self._before_filter, "allowed_methods", None)
                                  )
        if allowed_methods:
            if type(allowed_methods) not in (list, tuple):
                allowed_methods = [allowed_methods.upper()]
            else:
                allowed_methods = [i.upper() for i in allowed_methods]
            if self._request.method.upper() not in allowed_methods:
                raise MethodNotAllowed(', '.join(allowed_methods))
        return True

    def _view_wrapper(self, action_func, *args, **kwargs) -> HttpResponse:
        """
        wrap the view function, here we call
        * _before_filter
        If before filter returns a response object, the game is over and we return the response object without
        calling the action itself.
        If `_before_filter` returns some other data, it is passed to `__wrap_after_filter` which is then returned.
        Depending on the response from `_before_filter`, different rendering methods will be used.
        If `_before_filter` returns a string and call `__wrapped_print`, we will go to print, if `_before_filter` returns a dict, we will
        process it as context data and call `__wrapped_render`.

        If there is an error in `_before_filter`, we call `_on_exception` and then proceed to render the data returned from
        that, using the paradigm above - meaning text calls `__wrapped_print` and dict calls `__wrapped_render`.
        The `_after_filter` is skipped if `_on_exception` is called.

        :param action_func: The action function in question
        :return: an HttpResponse object
        """
        self._action_name = self._get_action_name(action_func)
        self._action_func = action_func

        if hasattr(action_func, 'ignore_ajax'):
            warnings.warn("action.ignore_ajax is deprecated, remove 2017-01-01", DeprecationWarning)
            self._no_ajax_prefix = self._no_ajax_prefix or getattr(action_func, 'ignore_ajax', False)
        else:
            self._no_ajax_prefix = self._no_ajax_prefix or getattr(action_func, 'no_ajax_prefix', False)

        self._action_name_sans_prefix = self._get_action_name(action_func, with_prefix=False)

        try:
            self._check_http_method_access(action_func)
        except MethodNotAllowed as e:
            return HttpResponseNotAllowed(str(e))

        send_args = {}
        if hasattr(action_func,'mimetype'):
            send_args['mimetype'] = action_func.mimetype
        if hasattr(action_func,'charset'):
            send_args['charset'] = action_func.charset

        try:
            # run before filter
            before_filter_response = self.__run_before_filter(action_func=action_func)
            if issubclass(before_filter_response.__class__, HttpResponse):
                return before_filter_response

            # run the actual action
            renderer = self.__run_action(action_func=action_func, renderer_args=send_args, *args, **kwargs)
            if issubclass(renderer.__class__, HttpResponse):
                return renderer

            try:
                renderer_context = renderer.get_context()
                if isinstance(renderer_context,dict) and isinstance(self._template_context,dict):
                    self._template_context.update(renderer.get_context())
                    renderer.update(self._template_context)
            except Exception as e:
                raise ValueError("Error applying before_filter data to action: %s." % e)

            after_filter_response = self.__run_after_filter(renderer=renderer, action_func=action_func)
            if issubclass(after_filter_response.__class__,HttpResponse):
                return after_filter_response

            self._response.status_code = renderer.status_code

        except Exception as exception:
            response = self._on_exception(request=self._request, exception=exception)

            if response is None:
                raise exception.with_traceback(sys.exc_info()[-1])
            else:
                if isinstance(response, dict):
                    renderer = TemplateRenderer(data=response, template_name=self._get_error_template_path(), **send_args)
                elif isinstance(response, str):
                    renderer = TextRenderer(data=response, **send_args)
                else:
                    return response

                self._response.status_code = 500

        rendered_response = renderer.render(self)
        if issubclass(rendered_response.__class__,HttpResponse):
            return rendered_response

        self._set_mimetype(mimetype=renderer.mimetype, charset=renderer.charset)
        self._response.content = rendered_response
        return self._response

    def __run_action(self, action_func, renderer_args, *args, **kwargs) -> Union[Tuple[Renderer,int], HttpResponse]:
        """

        :param action_func:
        :param args:
        :param kwargs:
        :return: a tuple with the action response and an http status code
        """
        if hasattr(self, 'do_not_pass_request'):
            action_response = action_func(*args, **kwargs)
        else:
            action_response = action_func(self._request, *args, **kwargs)

        if issubclass(action_response.__class__, HttpResponse):
            return action_response
        #######################################################

        action_response, status_code = self.__split_action_status_and_result(action_response, default_status_code=200)

        if issubclass(action_response.__class__, Renderer):
            renderer = action_response
            if renderer.status_code is None:
                renderer.status_code = status_code
        else:
            renderer = ActionController.default_renderer(data=action_response, status_code=status_code, **renderer_args)
            renderer.update(action_response)

        return renderer

    def __run_before_filter(self, action_func) -> Optional[HttpRequest]:
        """
        This calls `_before_filter` and updates the `template_context`.
        If the response from `_before_filter` is an `HttpResponse`, we return this
        without calling the action function.
        Anything returned from `_before_filter` that is not a `dict` or  subclass of `HttpResponse`, will be ignored.
        
        If the request contains `Accept: application/json`, the data returned from the action will be rendered as json.
        
        :param action_func:
        :param args:
        :param kwargs:
        :return:
        """
        if getattr(self, '_before_filter_runonce', False) == False and getattr(action_func,'disable_filters', False) == False:
            self._before_filter_runonce = True

            filter_response = self._before_filter(self._request)

            if issubclass(filter_response.__class__, Renderer):
                renderer = filter_response
                filter_response = renderer.render(self)

            if issubclass(filter_response.__class__, dict):
                self._template_context.update(filter_response)
            elif issubclass(filter_response.__class__,HttpResponse):
                return filter_response

        return None

    def __run_after_filter(self, action_func, renderer:Renderer)-> Optional[HttpResponse]:
        if not getattr(self, '_after_filter_runonce', False) and not getattr(action_func,'disable_filters', False):
            self._after_filter_runonce = True
            self._template_context = renderer.get_context()
            filter_response = self._after_filter(request=self._request)

            if issubclass(filter_response.__class__,HttpResponse):
                return filter_response
            elif filter_response is not None:
                try:
                    renderer.update(filter_response)
                except Exception as e:
                    raise ValueError("_after_filter tried to update existing data, but there was an error: %s." % e)

        return None

            
    def _before_filter(self, request) -> Union[None,dict,HttpResponse,Renderer]:
        """If overridden, runs before every action.
        This method is useful to add some additional data to all your actions, set instance variables and
        also verify a user's access to all actions in this controller.

        Code example:
        {{{
            @login_required
            def _before_filter(self):
                self.my_items = Item.objects.filter(user=request.user)
                return {
                    "page_title": "Item Page"
                }
            def get_item(self, request, pk):
                item = get_object_or_404(self.my_items, pk=pk)
                return {"item":item}
        }}}

        {{{
            def _before_filter(self):
                if self._action_name != 'login' and not self._request.user.is_authenticated:
                    return self._redirect(action='login')
                return None
        }}}
        :return: Either a dictionary with new data to add to the context, or an HttpResponse that will immediately be returned, without touching the `action` code.

        """
        return None
        
    def _after_filter(self, request):
        """
        This method is called after the actual `action` function has executed, and can be used to
        massage data returned by the `action` or add new data. The _after_filter function has access
        to data returned by the `action` through the `self._template_context` variable.
        :param request:
        :return:
        """
        return None

    def _before_render(self, request):
        """
        This function is currently not in use at all, and it will probably disappear.
        I guess the idea was to do something just before the renderer fires, but that seems
        to be what `_after_filter` does.
        :param request:
        :return:
        """
        return None

    def _on_exception(self, request, exception) -> Union[None,dict,HttpResponse]:
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
    
    def _set_mimetype(self, mimetype, charset = 'utf8'):
        if mimetype is not None:
            if charset is None:
                charset = self._response.charset
            self._response['Content-Type'] = "%s; charset=%s" % (mimetype, charset)

    @staticmethod
    def __split_action_status_and_result(result, default_status_code=None):
        """
        If an action returns a tuple of 2 values with the second value being an integer.
        :param result:
        :param default_status_code:
        :return:
        """
        status_code = default_status_code
        if isinstance(result, tuple) and len(result)==2 and isinstance(result[1],int):
            result, status_code = result
        return result, status_code

    def _as_auto_response(self, data, **kwargs):
        """determine the renderer from the requests' Accept: header"""
        return self._get_renderer_for_request(data, **kwargs)

    def _as_json(self, data, status_code=None, charset=default_charset, json_encoder=json_default_encoder, default=None, **kwargs):
        """Render the returned dictionary as a JSON object. Accepts the json.dumps `default` argument for a custom encoder."""
        if default:
            class CustomJSONEncoder(JSONEncoder):
                pass
            CustomJSONEncoder.default = default
            json_encoder = CustomJSONEncoder

        data, status_code = self.__split_action_status_and_result(data, status_code)

        return JSONRenderer(data, json_default_encoder=json_encoder, charset=charset, status_code=status_code)

    def _as_yaml(self, data, default_flow_style=yaml_default_flow_style, status_code=None, **kwargs):
        """Render the returned dictionary as a YAML object."""
        data, status_code = self.__split_action_status_and_result(data, status_code)
        return YAMLRenderer(data=data, default_flow_style=default_flow_style, charset=kwargs.pop('charset', default_charset), status_code=status_code)

    def _print(self, text, mimetype = 'text/plain', charset=default_charset):
        text, status_code = self.__split_action_status_and_result(text)
        return TextRenderer(data=text, mimetype=mimetype, charset=charset, status_code=status_code)

    def _get_flash(self):
        if self._flash_cache is None:
            from .flash import FlashManager
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
        
    
    def _render(self, dictionary=None, mimetype="text/html", charset=default_charset, **kwargs):
        """
            Render the provided dictionary using the default template for the given action.
            The keyword argument 'mimetype' may be used to alter the response type.

            The template context will be populated with the following data:
            request, controller_name, controller_actions (all actions), action_name (current_action), controller_helper, flash (flash messages)
        """
        data, status_code = self.__split_action_status_and_result(dictionary)
        return TemplateRenderer(data=dictionary, mimetype=mimetype, charset=charset, status_code=status_code, **kwargs)

    def _redirect(self, to_url = None, controller = None, action = None, named_url  = None, url_params = None, url_args=None, url_kwargs=None, permanent=False, **kwargs):
        """
        :param to_url: a URL to redirect to, other arguments will not be used if this is specified
        :param controller: a controller class or name, if not this one
        :param action: an action name - if a controller is not specified, the action will be in the current controller
        :param named_url: A named URL in django
        :param url_params: The query string params
        :param url_args: the list arguments for this URL, this will be used to build the URL within django's urlresolvers
        :param url_kwargs: the dict arguments for this URL, this will be used to build the URL within django's urlresolvers
        :param permanent: is this a permanent redirect? (301=permanent, 302=temporary)
        :param kwargs:
        :return: the HttpResponse with a redirecting content
        """
        if to_url is None:
            to_url = self._helper.url_for(
                controller=controller, action=action,
                named_url=named_url,
                url_params=url_params,
                url_args=url_args,
                url_kwargs=url_kwargs
            )
        return RedirectRenderer(to_url=to_url, permanent=permanent)
    _go = _redirect
    
    def _permanent_redirect(self, to_url=None, controller = None, action = None, named_url  = None, url_params = None, url_args=None, url_kwargs=None, permanent=False):
        """
        see `_redirect`
        """
        return self._go(permanent=True, **vars())
