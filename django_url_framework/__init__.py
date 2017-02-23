VERSION = (0, 3, 11)

try:
    from django_url_framework.site import Site
    from django_url_framework.controller import ActionController
    from django_url_framework.exceptions import InvalidActionError
    from django_url_framework.exceptions import InvalidControllerError
    from django_url_framework.helper import ApplicationHelper
    site = Site()
except ImportError:
    #todo this is an ugly hack for setuptools to load version, fix
    pass

# Dynamically calculate the version based on VERSION tuple
if len(VERSION)>2 and VERSION[2] is not None:
    str_version = "%d.%d.%s" % VERSION[:3]
else:
    str_version = "%d.%d" % VERSION[:2]

__version__ = str_version

def reraise(exception, info=None):
    import sys
    raise exception, None, sys.exc_info()[-1]

