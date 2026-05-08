import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from api.models import Actividad, Subtarea
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
user = User.objects.first()

hoy = timezone.localdate()
proxima_semana = hoy + timedelta(days=7)

print("Hoy:", hoy)

subtareas_qs = Subtarea.objects.filter(actividad__usuario=user).select_related('actividad')
print("Total subtareas del usuario:", subtareas_qs.count())

vencidas = subtareas_qs.filter(fecha_objetivo__lt=hoy, completada=False)
print("Vencidas:", vencidas.count())

de_hoy = subtareas_qs.filter(fecha_objetivo=hoy)
print("De Hoy:", de_hoy.count())

print("Subtareas de hoy:")
for s in de_hoy:
    print(f" - {s.titulo} (estado: {s.estado}, completada: {s.completada})")

