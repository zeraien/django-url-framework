class URLFrameworkError(Exception): pass
class ConfigurationError(URLFrameworkError): pass
class InvalidActionError(URLFrameworkError): pass
class InvalidControllerError(URLFrameworkError): pass
class MethodNotAllowed(URLFrameworkError): pass
