"""
WSGI config for PlaNET project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os, sys
from django.core.wsgi import get_wsgi_application
apache_configuration= os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)
sys.path.append(workspace)
sys.path.append(project)


# Add the path to 3rd party django application and to django itself.
sys.path.append('/home/sergio/code/PlaNET')
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.apache.override'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


