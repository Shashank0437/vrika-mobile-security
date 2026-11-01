"""
WSGI config for Vrika project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""
import os
import warnings

from django.core.wsgi import get_wsgi_application

from whitenoise import WhiteNoise

from . import settings


warnings.filterwarnings('ignore', category=UserWarning, module='cffi')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vrika_mobile_security.Vrika.settings')

if settings.RUNSERVER:
    root = os.path.join(settings.BASE_DIR, 'static')
    autorefresh = True
else:
    root = settings.STATIC_ROOT
    autorefresh = False
application = WhiteNoise(
    get_wsgi_application(),
    root=root,
    prefix='static/',
    autorefresh=autorefresh)
