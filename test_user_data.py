import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from api.models import Actividad, Subtarea
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
users = User.objects.all()

hoy = timezone.localdate()

for user in users:
    print(f"\nUser: {user.email}")
    sub_count = Subtarea.objects.filter(actividad__usuario=user).count()
    act_count = Actividad.objects.filter(usuario=user).count()
    print(f"Total Subtareas: {sub_count}, Total Actividades: {act_count}")
    
    subtareas_qs = Subtarea.objects.filter(actividad__usuario=user).select_related('actividad')
    vencidas = subtareas_qs.filter(fecha_objetivo__lt=hoy, completada=False)
    de_hoy = subtareas_qs.filter(fecha_objetivo=hoy)
    proximas = subtareas_qs.filter(fecha_objetivo__gt=hoy, completada=False)
    print(f"Vencidas: {vencidas.count()}, Hoy: {de_hoy.count()}, Proximas: {proximas.count()}")

