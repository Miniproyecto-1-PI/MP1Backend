from django.contrib import admin
from .models import Actividad, Subtarea


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'fecha_entrega', 'created_at']
    search_fields = ['titulo', 'descripcion']
    list_filter = ['fecha_entrega']


@admin.register(Subtarea)
class SubtareaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'actividad', 'completada', 'orden']
    list_filter = ['completada', 'actividad']
    search_fields = ['titulo']
