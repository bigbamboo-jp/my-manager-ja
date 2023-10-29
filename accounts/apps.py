from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'accounts'
    # verbose_name = 'User Management'
    verbose_name = 'ユーザー管理'

    def ready(self):
        from . import signals
        signals.__name__
