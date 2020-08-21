VERSION = (0, 5, 3)
default_app_config = 'django_url_framework.apps.URLFrameworkAppConfig'


# Dynamically calculate the version based on VERSION tuple
if len(VERSION)>2 and VERSION[2] is not None:
    str_version = "%d.%d.%s" % VERSION[:3]
else:
    str_version = "%d.%d" % VERSION[:2]

__version__ = str_version

def reraise(exception, info=None):
    import sys
    raise exception.with_traceback(sys.exc_info()[-1])

try:
    from .site import Site
    from .controller import ActionController
    from .exceptions import InvalidActionError
    from .exceptions import InvalidControllerError
    from .helper import ApplicationHelper
    site = Site()
except ImportError as e:
    #todo this is an ugly hack for setuptools to load version, fix
    print(e)

