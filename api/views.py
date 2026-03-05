from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Actividad, Subtarea
from .serializers import ActividadSerializer, SubtareaSerializer


def test_endpoint(request):
    return JsonResponse({
        "message": "API funcionando correctamente 🚀"
    })


class ActividadViewSet(viewsets.ModelViewSet):
    queryset = Actividad.objects.all().order_by('-created_at')
    serializer_class = ActividadSerializer


@api_view(['GET', 'POST'])
def subtareas_list(request, actividad_id):
    if request.method == 'GET':
        subtareas = Subtarea.objects.filter(actividad_id=actividad_id).order_by('orden')
        serializer = SubtareaSerializer(subtareas, many=True)
        return Response(serializer.data)
    
    if request.method == 'POST':
        actividad = Actividad.objects.get(pk=actividad_id)
        serializer = SubtareaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(actividad=actividad)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def actividades_hoy(request):
    hoy = datetime.now().date()
    actividades = Actividad.objects.filter(fecha_entrega=hoy).order_by('created_at')
    serializer = ActividadSerializer(actividades, many=True)
    return Response({
        'count': actividades.count(),
        'actividades': serializer.data
    })