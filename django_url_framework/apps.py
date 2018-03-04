from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class URLFrameworkAppConfig(AppConfig):
    name = 'django_url_framework'
    verbose_name = ugettext_lazy("Django URL Framework")
