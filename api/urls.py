from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import test_endpoint, ActividadViewSet, subtareas_list, subtarea_detail, actividades_hoy

router = DefaultRouter()
router.register(r'actividades', ActividadViewSet)

urlpatterns = [
    path('health/', test_endpoint),
    path('actividades/hoy/', actividades_hoy, name='actividades-hoy'),
    path('actividades/<int:actividad_id>/subtareas/', subtareas_list, name='subtareas-list'),
    path('subtareas/<int:pk>/', subtarea_detail, name='subtarea-detail'),
    path('', include(router.urls)),
]