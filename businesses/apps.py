from django.apps import AppConfig


class BusinessesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'businesses'
    verbose_name = 'Businesses'  # This will be displayed in the admin panel
