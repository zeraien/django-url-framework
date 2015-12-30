import logging
import re
import dircache
import imp
import os
from functools import wraps
from django.conf import settings

from django_url_framework.helper import ApplicationHelper
from django_url_framework.controller import ActionController
from django_url_framework.controller import InvalidControllerError
from django_url_framework.controller import InvalidActionError
from django_url_framework.controller import get_actions
from django_url_framework.controller import _patterns
from django_url_framework.controller import get_action_name
from django_url_framework.controller import get_controller_name
from django_url_framework.controller import get_controller_urlconf

from django.utils.translation import ugettext as _
from django.http import Http404
from django.conf.urls import include, url

from importlib import import_module


class Site(object):
    def __init__(self):
        self.controllers = {}
        self.helpers = {}
        self.logger = logging.getLogger(__name__)

    def autodiscover(self, include_apps = [], exclude_apps = []):
        """Autodiscover all urls within all applications that regex match any entry in 'include_apps'
        and exclude any in 'exclude_apps'.
        """
        
        if type(include_apps) not in (list, tuple):
            include_apps = (include_apps,)
        if type(exclude_apps) not in (list, tuple):
            exclude_apps = (exclude_apps,)
        
        if len(include_apps) == 0:
            include_apps = settings.INSTALLED_APPS
        
        for app in settings.INSTALLED_APPS:
            must_skip = False
            if app.endswith('django_url_framework'):
                continue
            
            for inc in include_apps:
                if re.search(inc, app):
                    must_skip = False
                    break
                else:
                    must_skip = True
            for excl in exclude_apps:
                if re.search(excl, app):
                    must_skip = True
                    break
            if must_skip:
                continue
            try:
                available_controllers = []
                app_path = import_module(app).__path__
                if app_path[0][-1] != os.path.sep:
                    app_path[0] = app_path[0]+os.path.sep
                    
                for f in dircache.listdir(app_path[0]):
                    if f.endswith('_controller.py'):
                        available_controllers.append(f[:-14])
                self.load_controllers(app_path, available_controllers)
            except AttributeError, e:
                self.logger.exception(e)
                continue
                
    def load_controllers(self, app_path, controllers):
        found_controller, found_helper = (None, None)
        
        for controller_file in controllers:
            """Load controller"""
            try:
                found_controller = imp.find_module('%s_controller' % controller_file, app_path)
            except ImportError, e:
                self.logger.warning("Failed to find proper controller in %s" % controller_file, exc_info=True)
                continue
            else:
                controller_module = imp.load_module('%s_controller' % controller_file, *found_controller)
                self.logger.debug("Loaded controller from %s" % controller_file)
                for controller_class_name in dir(controller_module):
                    # test_name = '%sController' % ''.join([i.title() for i in controller_file.split('_')])
                    if not controller_class_name.endswith('Controller'):
                        continue
                        
                    controller_class = getattr(controller_module, controller_class_name)
                    
                    if controller_class != ActionController and issubclass(controller_class, ActionController):
                        controller_name = get_controller_name(controller_class)
                        if controller_name in self.controllers:
                            continue
                            
                        self.controllers[controller_name] = controller_class
            
                        """Load helper"""
                        try:
                            found_helper = imp.find_module('%s_helper' % controller_file, app_path)
                        except ImportError, e:
                            self.logger.debug("No helper found for %s" % controller_name)
                            continue
                        else:
                            helper_module = imp.load_module('%s_helper' % controller_file, *found_helper)
                            self.logger.debug("Loaded helper for %s" % controller_name)
                            helper_class = getattr(helper_module ,'%sHelper' % controller_file.title(), None)
                            if helper_class and issubclass(helper_class, ApplicationHelper):
                                self.helpers[controller_name] = helper_class
                        finally:
                            if found_helper:
                                found_helper[0].close()
            finally:
                if found_controller:
                    found_controller[0].close()
            
    def _get_urls(self):
        urlpatterns = _patterns()
        
        for controller_name, controller_class in self.controllers.items():
            urlpatterns += _patterns(url(r'^%(controller)s/' % {'controller':controller_name}, include(get_controller_urlconf(controller_class, site=self))))
        return urlpatterns
    urls = property(_get_urls)
