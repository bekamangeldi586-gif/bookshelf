from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library'
    
    def ready(self):
        # Import signals to create groups/users/permissions after migrations
        try:
            from . import signals  # noqa: F401
        except Exception:
            # during management commands or migrations this may fail; ignore
            pass
