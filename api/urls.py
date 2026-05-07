from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    test_endpoint,
    ActividadViewSet,
    subtareas_list,
    subtarea_detail,
    subtarea_update_status,
    actividades_hoy,
    actividad_progreso,
    registro_view,
    login_view,
    me_view,
    actualizar_perfil_view,
    verificar_conflicto,
    carga_diaria,
)

router = DefaultRouter()
router.register(r'actividades', ActividadViewSet, basename='actividad')

urlpatterns = [
    path('health/', test_endpoint),

    # Auth
    path('auth/registro/', registro_view, name='registro'),
    path('auth/login/', login_view, name='login'),
    path('auth/me/', me_view, name='me'),
    path('auth/perfil/', actualizar_perfil_view, name='actualizar-perfil'),

    # Vista Hoy
    path('actividades/hoy/', actividades_hoy, name='actividades-hoy'),

    # Subtareas
    path('actividades/<int:actividad_id>/subtareas/', subtareas_list, name='subtareas-list'),
    path('subtareas/<int:pk>/', subtarea_detail, name='subtarea-detail'),
    path('subtareas/<int:pk>/status/', subtarea_update_status, name='subtarea-update-status'),

    # Progreso por actividad (US-10)
    path('actividades/<int:actividad_id>/progreso/', actividad_progreso, name='actividad-progreso'),

    # Conflicto de sobrecarga
    path('conflicto/verificar/', verificar_conflicto, name='verificar-conflicto'),
    path('conflicto/carga-diaria/', carga_diaria, name='carga-diaria'),

    # Router (actividades CRUD)
    path('', include(router.urls)),
]