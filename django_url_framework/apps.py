from django.apps import AppConfig
from django.utils.translation import gettext_lazy


class URLFrameworkAppConfig(AppConfig):
    name = 'django_url_framework'
    verbose_name = gettext_lazy("Django URL Framework")
