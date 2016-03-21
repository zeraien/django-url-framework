The django-url-framework will help you get your django applications done faster.

[![Join the chat at https://gitter.im/zeraien/django-url-framework](https://badges.gitter.im/zeraien/django-url-framework.svg)](https://gitter.im/zeraien/django-url-framework?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

It automatically detects urls in a django application, similar to the way Ruby on Rails does it with the Controller-Action-View implementation.

Controllers are created in each django application with a predefined file naming scheme (`foo_controller.py`) and extending `ActionController`. The `ActionController` contains methods often used in a web context, and does common request-related processing.

Each application can have multiple controllers thus allowing for smaller classes in a larger application.

Each function not starting with an underscore becomes it's own action. By simply returning a dictionary from the action, it will be rendered with the template named using the `controller/action.html` naming scheme.

Each action and controller can override certain global settings such as using a custom template name or giving the action (or controller) a custom name.

## Install

From pypi:

```
pip install django-url-framework
```

Alternatively just check out the source here and run `python setup.py install`

## Add to your project

### settings.py

```python
INSTALLED_APPS = (
  ...,
  'django_url_framework',
  ...
)
```
### urls.py
```python
import django_url_framework
from django.conf import settings
from django.conf.urls import patterns, include

django_url_framework.site.autodiscover(settings.INSTALLED_APPS)

urlpatterns = patterns('',
    (r'^', include(django_url_framework.site.urls) ),
)
```

## Example

### Folder structure

```
project/
  app/
      cart_controller.py
      foo_controller.py
      templates/
           cart/
              add.html
              index.html
              remove.html
           foo/
              bar.html
```

### cart_controller.py & foo_controller.py

```python
from django_url_framework.controller import ActionController

class CartController(ActionController):
    def edit(self, request, id = None):
        return {}
    def remove(self, request, id):
        return {}
    def index(self, request):
      return {}
```

```python
from django_url_framework.controller import ActionController

class FooController(ActionController):
    def index(self, request, object_id = None):
        return {}
    def bar(self, request):
        return {}
    def bar__delete(self, request):
        return {}
```

### Result

The following URLs will be created:

```
/cart/ <- will go to *index action*
/cart/(\w+)/
/cart/edit/
/cart/edit/(\w+)/
/cart/remove/(\w+)/
/foo/
/foo/(\w+)/
/foo/bar/
/foo/bar/delete/
```

You can easily access your URLs using django's built-in `{% url ... %}` tag. Simply call `{% url cart_index %}` or `{% url cart_delete id %}` and it will work as you would expect.

There is also a helper tag for faster linking within the same controller.
`{% go_action remove %}` will take you to `/cart/remove/`. To use it, `{% load url_framework %}` in your templates.

### Controller names

The controller name is derived from it's class name, by converting camelcase into underscores.
For instance `FooController` is simple `foo`, while `FooBarController` becomes `foo_bar`.

You can give the controller a custom name with the `controller_name` parameter:
```python
class Controller(ActionController):
  controller_name = "foo"
```

### Template filenames

By default templates are stored in the subdirectory with the controller's name, and the templates are given the same filename as the action name.
If a request is determinned to be AJAX in nature, the template filename is prefixed with an underscore.
Example:
````python
class FooController(ActionController):
    def foo_action(self, request):
      return {}
```

File structure:
```
/foo/foo_action.html
/foo/_foo_action.html <--- for AJAX requests.
```

You can disable this prefixing on a per action or per controller level.

For all actions in a controller:
````python
class FooController(ActionController):
    no_ajax_prefix = True
```

For a single action:
````python
from django_url_framework.decorators.action_options
class FooController(ActionController):
    @no_ajax_prefix
    def foo_action(self, request):
      return {}
```


## Action names

````python
class FooController(ActionController):
    def action(self, request):
      return {}
```
Creates the following URL:
```
/controller/action/
```

Double underscores `__` in action names are converted to slashes in the urlconf, so: `action__name` becomes `/action/name/`.

````python
class Controller(ActionController):
    def action__foo(self, request):
      return {}
```
Creates the following URL:
```
/controller/action/foo/
```


### Decorate to name

You can also decorate functions to give them different names and prefixes and urls. See decorator package for more details, here is an example:
```python
@action_options.name("foo")
@action_options.prefix("prefix_")
def bar(self, request):
  return {}
```
will result in:
```
/controller/prefix_foo/
```

The action will now have the template `/controller/foo.html`. Prefixes do not affect template naming.

## Action parameters

Providing a third parameter to an action will create a URLconf for that parameter, like so:
````python
def action(self, request, object_id):
    return {}
```
Will allow you to call that action with:
```
/controller/action/(\w+)/ <--- parameter consisting of A-Za-z0-9_
```
If you make the argument optional, an additional URLconf entry is created allowing you to call the action without the third argument.
```python
def action(self, request, object_id = None):
    return {}
```
Results in:

```
/controller/action/
/controller/action/(\w+)/  <--- optional argument consisting of A-Za-z0-9_
```

### Decorate for custom parameters

You can also create your own custom parameters by using the `@url_parameters` decorator to the function.
```python
from django_url_framework.decorators.action_options import url_paramters
class Controller(ActionController):
    @url_parameters(r'(?P<year>\d{4})/(?P<month>\d\d)')
    def action(self, request, year, month):
        ...
        return {}
```
The above will create the following url patterns:
```
/controller/action/(?P<year>\d{4})/(?P<month>\d\d)
```
*Note the lack of trailing slash - you must provide this yourself.*

### Custom url for any action

You can write your own urlconf for each action, by decorating it with `@urlconf`.
```python
from django_url_framework.decorators.action_options import urlconf
class Controller(ActionController):
    @action_options.urlconf([
            r'^bar/(?P<year>\d{4})/$',
            r'^bar/(?P<year>\d{4})/(?P<month>\d\d)/$',
            r'^foo/(?P<year>\d{4})/(?P<month>\d\d)/(?P<day>\d\d)/$'
        ],
        do_not_autogenerate=True)
    def action(self, request, year, month=None, day=None):
        ...
        return {}
```
The above will create the following url patterns:
```
/controller/bar/(?P<year>\d{4})/
/controller/bar/(?P<year>\d{4})/(?P<month>\d\d)/$
/controller/foo/(?P<year>\d{4})/(?P<month>\d\d)/(?P<day>\d\d)/$
```

The `do_not_autogenerate` argument is **true** by default and will prevent any urls for this action
from being autogenerated. If `do_not_autogenerate` were to be set to false in the example below,
the following url would also be created:
```
/controller/action/
```
This URL would not actually work since the `year` argument is required the `action` function.

## Flash messages

The ActionController also has a _flash instance variable that allows you to send messages to the user that can survive a redirect. Simply use 

```python
self._flash.append("Message")

self._flash.error("Error message")
```

The flash messages can be either messages or error messages. The flash object is automatically exported into the context and you can use it as such:

```HTML+Django
{% if flash.has_messages %}
  {% for message in flash.get_and_clear %}

      {% if message.is_error %}<span class='icon-error'></span>{% endif %}

      <p class="{{message.type}}">{{message}}</p>
      
  {% endfor %}
{% endif }
```

## Before and After each action

You can override `_before_filter` and/or `_after_filter` to perform certain actions and checks before or after an action. Read more in `ActionController` docs.

These methods accept the "request" parameter which is an HTTP request object for this request.

```python
class AccountController(ActionController):

    def _before_filter(self, request):
        campaign_id = request.GET.get("campaign_id")
        try:
          self._campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
          self._campaign = None

```

You can disable the before and after filters by decorating any action with the `@disable_filters` decorator.

Example:
```python
from django_url_framework.decorators.action_options import disable_filters
@disable_filters
def action(self, request):
  return {}
```

One of the great features of django url framework is that you can require login for all actions in a controller by simply decorating the before_filter with a decorator to require logging in, see next section!

## Authentication

To require login on an action use the `@login_required` decorator provided by django-url-framework. The decorator also works on `_before_filter`.

```python
from django_url_framework.decorators import login_required
class AccountController(ActionController):

    @login_required
    def action(self, request):
        return {}
```

If the user isn’t logged in, redirect to `settings.LOGIN_URL`, passing the current absolute path in the query string. Example: `/accounts/login/?next=/polls/3/`.
`login_required()` also takes an optional `login_url` parameter. Example:

```python
from django_url_framework.decorators import login_required
class AccountController(ActionController):

    @login_required(login_url="/login/")
    def action(self, request):
        return {}
```

By default, the path that the user should be redirected to upon successful authentication is stored in a query string parameter called "next". If you would prefer to use a different name for this parameter, `login_required()` takes an optional `redirect_field_name` parameter.

Additionally you can use `@superuser_required`, `@permission_required(permission_instance)` and `@must_be_member_of_group(group_name="some_group")`.

## Only POST? (or GET or anything...)
You can limit what http methods a function can be called with.

The example below limits the `update` action to only **POST** and **DELETE** http methods.

```python
from django_url_framework.decorators import http_methods
class Controller(ActionController):
    @http_methods.POST
    @http_methods.DELETE
    def update(self, request):
        return {}
```

By default all actions can be called with all http methods.

## Custom template extensions
When using jade or something similar you can specify a custom extension for all templates in the controller.

```python
class FooController(ActionController):
    #custom extension for all templates in this controller
    template_extension = "jade"
```
