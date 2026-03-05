from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import test_endpoint, ActividadViewSet, subtareas_list

router = DefaultRouter()
router.register(r'actividades', ActividadViewSet)

urlpatterns = [
    path('health/', test_endpoint),
    path('', include(router.urls)),
    path('actividades/<int:actividad_id>/subtareas/', subtareas_list, name='subtareas-list'),
]