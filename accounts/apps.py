from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'accounts'
    # verbose_name = 'Authentication and Authorization (2)'
    verbose_name = '認証と認可 (2)'

    def ready(self):
        from . import signals
        signals.__name__
