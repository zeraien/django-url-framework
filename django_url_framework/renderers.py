import json

from django.core.serializers.json import DjangoJSONEncoder

import django_url_framework #for type hinting

import pprint
from abc import ABC, abstractmethod

from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

default_charset = "utf8"
class Renderer(ABC):
    def __init__(self, data, mimetype=None, charset=default_charset, status_code=200, **kwargs):
        self._data = data
        self.mimetype=mimetype
        self.charset=charset
        self.status_code=status_code

    def get_context(self):
        return self._data

    @abstractmethod
    def render(self, controller:'django_url_framework.controller.ActionController')->str:
        pass

    def update(self, data)->None:
        if isinstance(data,dict):
            self._data.update(data)
        else:
            raise ValueError("expecting a dictionary")

class TemplateRenderer(Renderer):
    def __init__(self, data, template_name=None, **kwargs):
        super(TemplateRenderer, self).__init__(data=data, **kwargs)
        self._template_name = template_name

    def get_template_name(self, controller:'django_url_framework.controller.ActionController'):
        if not self._template_name:
            template_replacement_data = {'controller':controller._template_prefix,
                                         'action':controller._action_name,
                                         'ext':controller._template_extension}

            if controller._is_ajax and controller._no_ajax_prefix==False:
                if hasattr(controller._action_func, 'ajax_template_name'):
                    self._template_name = controller._action_func.ajax_template_name
                else:
                    self._template_name = controller._ajax_template_string % template_replacement_data
            elif hasattr(controller._action_func,'template_name'):
                self._template_name = controller._action_func.template_name
            else:
                self._template_name = controller._template_string % template_replacement_data
        return self._template_name

    def render(self, controller):
        from django.template import loader
        dictionary = self._data
        if dictionary is None:
            dictionary = {}

        dictionary.update({
            'request':controller._request,
            'controller_name':controller._controller_name,
            'controller_actions':list(controller._actions.keys()),
            'action_name':controller._action_name,
            'controller_helper':controller._helper,
            'flash': controller._flash,
        })


        return  loader.render_to_string(template_name=self.get_template_name(controller=controller),
                                         context=self._data,
                                         request=controller._request)

class TextRenderer(Renderer):
    def __init__(self, data, mimetype="text/plain", **kwargs):
        super(TextRenderer, self).__init__(data=data, mimetype=mimetype, **kwargs)
    def render(self,  controller):
        if isinstance(self._data,str):
            return self._data
        return pprint.pformat(self._data)

    def update(self, data):
        if isinstance(self._data, dict) and isinstance(data, dict):
            super(TextRenderer, self).update(data=data)
        elif isinstance(data,str):
            self._data = data

class YAMLRenderer(Renderer):
    def __init__(self, data, default_flow_style=None, **kwargs):
        super(YAMLRenderer, self).__init__(data=data, mimetype="application/yaml", **kwargs)
        self._default_flow_style = default_flow_style
    def render(self, controller):
        import yaml
        return yaml.dump(self._data, default_flow_style=self._default_flow_style)


class JSONRenderer(Renderer):
    def __init__(self, data, json_default_encoder=DjangoJSONEncoder, **kwargs):
        super(JSONRenderer, self).__init__(data=data, mimetype="application/json", **kwargs)
        self._json_default_encoder = json_default_encoder

    def update(self, data):
        if isinstance(self._data, dict) and isinstance(data, dict):
            super(JSONRenderer, self).update(data=data)

    def render(self, controller):
        return json.dumps(self._data, cls=self._json_default_encoder)

class RedirectRenderer(Renderer):
    def __init__(self, to_url, permanent=False, **kwargs):
        self.permanent=permanent
        self.to_url = to_url
        super(RedirectRenderer, self).__init__(data=None,**kwargs)

    def update(self, data) -> None:
        pass #noop

    def render(self, controller):
        if self.permanent:
            return HttpResponsePermanentRedirect(self.to_url)
        else:
            return HttpResponseRedirect(self.to_url)

