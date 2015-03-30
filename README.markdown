The django-url-framework will help you get your django applications done faster.

It automatically detects urls in a django application, similar to the way Ruby on Rails does it with the Controller-Action-View implementation.

Controllers are created in each django application with a predefined file naming scheme (*foo_controller.py*) and extending ActionController. The ActionController contains methods often used in a web context, and does common request-related processing.

Each application can have multiple controllers thus allowing for smaller classes in a larger application.

Each function not starting with an underscore becomes it's own action. By simply returning a dictionary from the action, it will be rendered with the template named using the *controller/action.html* naming scheme.

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
class CartController(ActionController):
   def edit(self, request, id = None):
      return {}
   def remove(self, request, id)
      return {}
   def index(self, request):
      return {}

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

You can easily access your URLs using django's built-in *url* tag. Simply call *{% url cart_index %}* or *{% url cart_delete id %}* and it will work as you would expect.

There is also a helper tag for faster linking within the same controller.
*{% go_action remove %}* will take you to */cart/remove/*. To use it, load *url_framework* in your templates.

## Action names and parameters

In action names, double underscores __ are converted to slashes in the urlconf, so: *action__name* becomes */action/name/*.

Providing a third parameter to an action will create a URLconf for that parameter, like so:
````python
def action(self, request, object_id):
    return {}
```
Will allow you to call that action with:
```
/controller/action/(\w+)/ <--- argument consisting of A-Za-z0-9_
```
If you make the argument optional, an additional URLconf entry is created allowing you to call the action without the numeric path.
```python
def action(self, request, object_id = None):
    return {}
```
Results in:

```
/controller/action/
/controller/action/(\w+)/  <--- optionalargument consisting of A-Za-z0-9_
```

## Flash

The ActionController also has a _flash instance variable that allows you to send messages to the user that can survive a redirect. Simply use 

```python
self._flash.append("Message")

self._flash.error("Error message")
```

The flash messages can be either messages or error messages. The flash object is automatically exported into the context and you can use it as such:

```HTML+Django
{% for message in flash.get_and_clear %}

    {% if message.is_error %}<span class='icon-error'></span>{% endif %}

    <p class="{{message.type}}">{{message}}</p>
    
{% endfor %}
```

## Before and After each action

You can override `_before_filter` and/or `_after_filter` to perform certain actions and checks before or after an action. Read more in `ActionController` docs.

These methods accept the "request" parameter which is an HTTP request object for this request.

For example, to require login on all actions in a single controller, use the login_required decorator provided by django-url-framework. The decorator also works on individual actions.

```python
from django_url_framework.decorators import login_required
class AccountController(ActionController):

    @login_required
    def _before_filter(self, request):
        pass
```

## Custom template extensions
When using jade or something similar you can specify a custom extension for all templates in the controller.

```python
class AccountController(ActionController):
    #custom extension for all templates in this controller
    template_extension = "jade"
```
