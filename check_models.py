import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps

models = apps.get_app_config('resilience_app').get_models()
print("Models loaded:")
for model in models:
    print(f"  - {model.__name__}")

# Also try direct import
try:
    from resilience_app.models import ConsentFormInvitation
    print("\nConsentFormInvitation imported successfully")
except ImportError as e:
    print(f"\nFailed to import ConsentFormInvitation: {e}")
