from .models import SystemSettings

def settings_context(request):
    return {
        'system_settings': SystemSettings.get_settings()
    }
