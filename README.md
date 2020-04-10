The django-url-framework will help you get your django applications done faster.

[![Documentation Status](https://readthedocs.org/projects/django-url-framework/badge/?version=latest)](https://django-url-framework.readthedocs.io/en/latest/?badge=latest)

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

django_url_framework.site.autodiscover(new_inflection_library=True)

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
           id_manager/
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

class IDManagerController(ActionController):
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

The latest version uses the `inflection` library, however to avoid breaking old code, this is still optional until 2021.

The biggest difference is that with `inflection`, `HTTPResponse` becomes `http_response`, while the old name would be `httpresponse`. I suggest enabling the `inflection` library for all new and existing projects. You can manually specify names for controllers whose name change would break your code, or disable the inflection library for those controllers using a flag.

You can give the controller a custom name with the `controller_name` parameter:
```python
class Controller(ActionController):
  controller_name = "foo"
```

Enable or disable the use of the new `inflection` library using a flag
```python
class Controller(ActionController):
  use_inflection_library = True
```

### Other useful controller settings

```python
class BarController(ActionController):
    
    # default filename extension for all templates
    template_extension = "pug" 
    
    # will require every template file to start with this string
    template_prefix = "foo_" 
    
    # will not look for templates in subdirectories, but in the root templates/ folder
    no_subdirectories = False 
    
    # do not prefix templates with `_` (underscore) when they are called using an AJAX request
    no_ajax_prefix = False 

    # Set a prefix for the controller's name, applies even if
    # you set controller_name (template name is based on controller_name, sans prefix)
    # NOTE: The urlconf name will not include the prefix, only the actual URL itself
    # Thus: FooController.list will have the URL /prefixed_foo/list/, but the url name will be
    # `foo_list`.
    controller_prefix = "prefixed_" 
    
    # completely override the name of the controller
    controller_name = "shopping_cart" 

    # When used with custom urlconf in actions, these arguments will not be passed to the action
    # example: "/<id:int>/<skip:bool>/" Only `id` will be passed to the `action`, while `skip` will not be.
    consume_urlconf_keyword_arguments = ['skip']

    # set a prefix for all the URLs in this controller
    # So, what normally would be `/controller/action/`, becomes `^prefix/controller/action/`
    urlconf_prefix:list = ["^prefix"]

    # A custom json encoder, subclassing JSONEncoder 
    json_default_encoder:JSONEncoder = None

    # use the yaml default flow style
    yaml_default_flow_style:bool = True

    # use the new inflection library to generate controller url
    # if this is None, will use the global setting, otherwise override this on a per controller basis
    use_inflection_library:Union[bool,None] = None

```

### Template filenames

By default templates are stored in the subdirectory with the controller's name, and the templates are given the same filename as the action name.
If a request is determinned to be AJAX in nature, the template filename is prefixed with an underscore.
Example:
```python
class FooController(ActionController):
    def foo_action(self, request):
      return {}
```

File structure:
```python
/foo/foo_action.html
/foo/_foo_action.html <--- for AJAX requests.
```

You can disable this prefixing on a per action or per controller level.

For all actions in a controller:
```python
class FooController(ActionController):
    no_ajax_prefix = True
```

For a single action:
```python
from django_url_framework.decorators.action_options
class FooController(ActionController):
    @no_ajax_prefix
    def foo_action(self, request):
      return {}
```


## Action names

```python
class FooController(ActionController):
    def action(self, request):
      return {}
```
Creates the following URL:
```
/controller/action/
```

Double underscores `__` in action names are converted to slashes in the urlconf, so: `action__name` becomes `/action/name/`.

```python
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
```python
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

### Decorate for JSON, YAML or Automatic

You can decorate any action to have a default renderer.
Instead of using `self._as_json` as before, you can just put a decorator like so:

```python
from django_url_framework.decorators import json_action
    @json_action(json_encoder=None)
    def action(self, request, year, month):
        ...
        return {}
```
Other decorators include `@yaml_action(default_flow_style:bool)` and `@auto()`.
YaML is self-explanatory, however `@auto` is a bit interesting, it will automatically determine the renderer based on the `HTTP_ACCEPT` header. 

*Warning* - if you expose raw data in your actions, that normally would be massaged inside a Server-Side template, DO NOT USE the `@auto` decorator as this allows an attacker to download raw data from your server.
However, if your responses are designed for an API, the `@auto` decorator will enable the API client to request data as it sees fit, for example, it can request a Server-Side rendered HTML, or the same data as JSON or YaML.

Here is a list of supported renderers:
- text/html - `TemplateRenderer` - renders using the appropriate Django template
- text/plain - `TextRenderer` - prints text data as is, or prints object types using `pprint.pformat`
- application/json - `JSONRenderer` - renders data as JSON
- application/yaml - `YamlRenderer` - renders data as YaML

`@auto()` accepts the following parameters:
- json_encoder
- yaml_default_flow_style
The work the same as if passed to `@json_action()` or `@yaml_action()`

### Set HTTP Status Codes easily

Any action can return a tuple of two items, the second item should be an `int` and will become the HTTP status code for your response.

```python
    @json_action()
    def update(self, request, year, month):
        ...
        return False, 304 #not modified

    @json_action()
    def create(self, request, year, month):
        ...
        return True, 201 #created
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

The ActionController also has a `_flash` instance variable that allows you to send messages to the user that can survive a redirect. Simply use 

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

Another example makes it easy to limiting access to a subset of data based on the logged in user for the whole controller.

```python
from django_url_framework.decorators import login_required
class ItemController(ActionController):
    @login_required()
    def _before_filter(self):
        self.my_items = Item.objects.filter(user=request.user)
        self.my_products = Product.objects.filter(item__in=self.my_items)
        return {
            "page_title": "Item Page"
        }
    def item(self, request, pk):
        item = get_object_or_404(self.my_items, pk=pk)
        return {"item":item}
    def product(self, request, pk):
        item = get_object_or_404(self.my_products, pk=pk)
        return {"product":product}


```

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
