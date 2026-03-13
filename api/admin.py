from django.contrib import admin
from .models import Actividad, Subtarea, PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'limite_diario_horas', 'created_at']
    search_fields = ['usuario__username']


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'usuario', 'fecha_entrega', 'created_at']
    search_fields = ['titulo', 'descripcion']
    list_filter = ['tipo', 'fecha_entrega', 'usuario']


@admin.register(Subtarea)
class SubtareaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'actividad', 'completada', 'horas_estimadas', 'fecha_objetivo', 'orden']
    list_filter = ['tipo', 'completada', 'actividad']
    search_fields = ['titulo']
