from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        try:
            from . import firebase as firebase_module
            firebase_module.initialize()
        except Exception:
            # Initialization failure should not prevent Django from starting.
            pass
