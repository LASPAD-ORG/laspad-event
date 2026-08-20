"""Réglages LOCAUX pour prévisualiser le planning (jamais utilisés en prod).
   - base SQLite temporaire
   - e-mails affichés dans la console (le lien magique s'imprime dans les logs)
"""
from config.settings_sqlite import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'planning@laspad.org'
