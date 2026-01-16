from django.apps import AppConfig


class AdeazeitConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adeazeit'

    def ready(self):
        # Register signal handlers (z.B. Cache-Invalidierung bei Holiday-Änderungen)
        from . import signals  # noqa: F401