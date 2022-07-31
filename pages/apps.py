from django.apps import AppConfig


class PagesConfig(AppConfig):
    name = 'pages'
    # verbose_name = 'Service'
    verbose_name = 'サービス'

    def ready(self):
        from . import signals
        signals.__name__
