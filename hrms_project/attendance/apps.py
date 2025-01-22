from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'

    def ready(self):
        """
        Import signals when the app is ready
        Make sure any custom configurations are loaded
        """
        pass  # Add any startup logic here
