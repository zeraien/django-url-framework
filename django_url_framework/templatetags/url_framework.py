from django import template
from django.utils.safestring import mark_safe
register = template.Library()


class UrlNode(template.Node):
    def __init__(self, named_url = None, action = None, extras = []):
        self.named_url = named_url
        self.action = action
        self.extras = extras
    def render(self, context):
        resolved_extras = []
        for extra in self.extras:
            resolved_extras.append(template.Variable(extra).resolve(context))
        return reverse_url(context['controller_helper'], named_url = self.named_url, action = self.action, extras = resolved_extras)

@register.tag
def go_action(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_data = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % token.contents.split()[0]
    return UrlNode(action=tag_data[1], extras=tag_data[2:])

@register.tag
def url_for(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_data = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires at least one argument" % token.contents.split()[0]
    return UrlNode(named_url='/'.join(tag_data[1:]))

def reverse_url(helper, named_url = None, action = None, extras = None):
    """Can be given parameters such as controller or action.
    Also accepts other unknown parameters such as 'id'.
    
    If given 'named_url', the URL is split using the '/' character and then processed into
    'controller', 'action' and 'id', in that order.
    
    If a part of the URL contains a ':', the value is split and the first part becomes the parameter key,
    while the second parameter value.
    
    Examples:
    
      /order/list/
                    => controller: order, action: list
      /order/show/4 
                    => controller: order, action: show, id: 4
      /products/    
                    => controller: products, action: index
      action:list 
                    => controller: The view controller, action: list
      action:list controller:produts 
                    => controller: products, action: list
      action:_delete item:bar
                    => controller: The view controller, action: _delete, item: bar
    """
    if named_url is not None:
        kwargs = {}
        url_parts = str(named_url).strip('/ ').split('/')
        url_part_order = ['controller', 'action', 'id']
        for url_part in url_parts:
            if ':' in url_part:
                name, value = url_part.split(':')
            elif len(url_part_order) > 0:
                name, value = (url_part_order.pop(0), url_part)
            kwargs[name] = value
        return helper.url_for(url_args=extras, **kwargs)
    else:
        return helper.url_for(controller=None, action=action, named_url=named_url, url_args=extras)

