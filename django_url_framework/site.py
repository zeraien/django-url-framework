import sys
import inspect
import logging
import re
import os
import importlib
import importlib.util

from django.apps import apps

from .helper import ApplicationHelper
from .controller import ActionController
from .controller import url_patterns
from .controller import get_controller_name
from .controller import get_controller_urlconf

from django.conf.urls import include, url

class Site(object):
    def __init__(self):
        self.controllers = {}
        self.helpers = {}
        self.logger = logging.getLogger("django_url_framework")
        self._use_inflection_lib = False

    def autodiscover(self, include_apps = [], exclude_apps = [], new_inflection_library=False):
        """Autodiscover all urls within all applications that regex match any entry in 'include_apps'
        and exclude any in 'exclude_apps'.
        :param exclude_apps: A list of django apps not to include in auto generation
        :param include_apps: A list of apps to include in auto generation - use this will no longer auto detect apps
        :param new_inflection_library: Use `inflection` library to generate URLs from Controller class names (recommended!). Will be the default in 2020.
        """
        self._use_inflection_lib = new_inflection_library
        
        if type(include_apps) not in (list, tuple):
            include_apps = (include_apps,)
        if type(exclude_apps) not in (list, tuple):
            exclude_apps = (exclude_apps,)
        
        if len(include_apps) == 0:
            include_apps = list(apps.app_configs.keys())
        
        for app_config in list(apps.app_configs.values()):

            must_skip = False
            app_name = app_config.name
            if app_name.endswith('django_url_framework'):
                continue
            
            for inc in include_apps:
                if re.search(inc, app_name):
                    must_skip = False
                    break
                else:
                    must_skip = True
            for excl in exclude_apps:
                if re.search(excl, app_name):
                    must_skip = True
                    break
            if must_skip:
                continue
            try:
                available_controllers = []
                app_path = app_config.path
                for f in self._yield_controller_files(app_path):
                    available_controllers.append(f)
                self._load_controllers(app_path=app_path,
                                      app_module_path=app_name,
                                      controllers=available_controllers,
                                      )
            except AttributeError as e:
                self.logger.exception(e)

    @staticmethod
    def _yield_controller_files(app_path):
        if sys.version_info>=(3,0):
            with os.scandir(app_path) as it:
                for entry in it:
                    if entry.name.endswith('_controller.py'):
                        yield entry.name[:-3]
        else:
            import dircache
            for f in dircache.listdir(app_path):
                if f.endswith('_controller.py'):
                    yield f[:-3]

    def _yield_controller_class(self, app_path, app_module_path, controller_file):
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("[LOADING] controller from %s.%s" % (app_module_path,controller_file))

        controller_module = None

        if sys.version_info<(3,1):
            found_controller = None
            import imp
            try:
                found_controller = imp.find_module(controller_file, [app_path])
            except ImportError:
                self.logger.warning("[FAIL] to find proper controller in %s" % controller_file, exc_info=True)
            else:
                controller_module = imp.load_module('%s' % controller_file, *found_controller)
            finally:
                if found_controller:
                    found_controller[0].close()

        else:
            controller_module = importlib.import_module('%s.%s' % (app_module_path,controller_file))

        if controller_module:
            for m in inspect.getmembers(controller_module, inspect.isclass):
                if re.search(r'Controller$',m[0]) and m[1].__module__ == controller_module.__name__:
                    controller_class = m[1]
                    if controller_class != ActionController and issubclass(controller_class, ActionController):
                        yield controller_class

    def _load_helper(self, controller_file, app_path, controller_name):
        """Load helper"""
        try:
            found_helper = importlib.util.find_spec('%s_helper' % controller_file, [app_path])
        except ImportError:
            pass
        else:
            helper_module = importlib.util.module_from_spec(found_helper)
            self.logger.debug("Loaded helper for %s" % controller_name)
            helper_class = getattr(helper_module ,'%sHelper' % controller_file.title(), None)
            if helper_class and issubclass(helper_class, ApplicationHelper):
                self.helpers[controller_name] = helper_class
        finally:
            if found_helper:
                found_helper[0].close()

    def _load_controllers(self, app_path, app_module_path, controllers):
        found_controller, found_helper = (None, None)
        
        for controller_file in controllers:
            """Load controller"""
            try:
                for controller_class in self._yield_controller_class(app_path=app_path,
                                                                     app_module_path=app_module_path,
                                                                     controller_file=controller_file):
                    controller_name = get_controller_name(controller_class)
                    self.controllers[controller_name] = controller_class

                    if controller_class.use_inflection_library is None:
                       controller_class.use_inflection_library = self._use_inflection_lib

                    if self.logger.isEnabledFor(logging.DEBUG):
                        self.logger.debug("[LOADED] %s as %s" % (controller_class.__name__, controller_name))

                    # self._load_helper(controller_file=controller_file,
                    #                   app_path=app_path,
                    #                   controller_name=controller_name)

            except ImportError:
                self.logger.warning("Failed to find proper controller in %s" % controller_file, exc_info=True)
            finally:
                if found_controller:
                    found_controller[0].close()
            
    def _get_urls(self):
        urlpatterns = url_patterns()
        
        for controller_name, controller_class in list(self.controllers.items()):
            urlpatterns += url_patterns(url(r'^%(controller)s/' % {'controller':controller_name}, include(get_controller_urlconf(controller_class, site=self))))
        return urlpatterns, None, 'django-url-framework'
    urls = property(_get_urls)
