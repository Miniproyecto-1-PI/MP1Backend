import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from api.models import Subtarea

for s in Subtarea.objects.all():
    print(f"Subtarea {s.id}: estado='{s.estado}', completada={s.completada}")

