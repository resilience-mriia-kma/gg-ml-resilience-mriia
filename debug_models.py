import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    import resilience_app.models as models_module
    import importlib
    importlib.reload(models_module)
    
    print("All attributes in models module:")
    for attr in dir(models_module):
        if not attr.startswith('_'):
            print(f"  - {attr}")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
