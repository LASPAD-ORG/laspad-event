from django.conf import settings

def site_settings(request):
    return {
        'SITE_URL':  getattr(settings, 'SITE_URL', 'https://events.laspad.org'),
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'LASPAD Event'),
    }
