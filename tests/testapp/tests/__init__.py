# Print django version.
import django
print(f'DJANGO-VERSION: {django.VERSION[0]}.{django.VERSION[1]}.{django.VERSION[2]}')

# Print python version.
import sys
print(f'PYTHON-VERSION: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')
