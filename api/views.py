from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from decimal import Decimal

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Actividad, Subtarea, PerfilUsuario
from .serializers import (
    ActividadSerializer,
    SubtareaSerializer,
    RegistroSerializer,
    LoginSerializer,
    UsuarioSerializer,
    PerfilUsuarioSerializer,
    ConflictoCheckSerializer,
)


def test_endpoint(request):
    return JsonResponse({
        "message": "API funcionando correctamente 🚀"
    })


# ──────────────────────────────────────────────
# Auth Views
# ──────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def registro_view(request):
    """Registrar un nuevo usuario."""
    serializer = RegistroSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Cuenta creada exitosamente',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'limite_diario_horas': float(user.perfil.limite_diario_horas),
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Iniciar sesión y obtener tokens JWT."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        # Asegurar que tenga perfil
        perfil, _ = PerfilUsuario.objects.get_or_create(
            usuario=user,
            defaults={'limite_diario_horas': 6.0}
        )

        return Response({
            'message': 'Inicio de sesión exitoso',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'limite_diario_horas': float(perfil.limite_diario_horas),
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Obtener datos del usuario autenticado."""
    user = request.user
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=user,
        defaults={'limite_diario_horas': 6.0}
    )
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'limite_diario_horas': float(perfil.limite_diario_horas),
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_perfil_view(request):
    """Actualizar configuración del perfil (ej: límite diario)."""
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=request.user,
        defaults={'limite_diario_horas': 6.0}
    )
    serializer = PerfilUsuarioSerializer(perfil, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Perfil actualizado',
            'limite_diario_horas': float(perfil.limite_diario_horas)
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Actividades — CRUD protegido por usuario
# ──────────────────────────────────────────────

class ActividadViewSet(viewsets.ModelViewSet):
    serializer_class = ActividadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo devuelve las actividades del usuario autenticado."""
        return Actividad.objects.filter(
            usuario=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Asigna el usuario autenticado al crear una actividad."""
        serializer.save(usuario=self.request.user)


# ──────────────────────────────────────────────
# Subtareas — CRUD protegido por usuario
# ──────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def subtareas_list(request, actividad_id):
    # Verificar que la actividad pertenece al usuario
    try:
        actividad = Actividad.objects.get(pk=actividad_id, usuario=request.user)
    except Actividad.DoesNotExist:
        return Response(
            {"detail": "Actividad no encontrada"},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        subtareas = Subtarea.objects.filter(actividad=actividad).order_by('orden')
        serializer = SubtareaSerializer(subtareas, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = SubtareaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(actividad=actividad)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def subtarea_detail(request, pk):
    try:
        subtarea = Subtarea.objects.get(pk=pk, actividad__usuario=request.user)
    except Subtarea.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SubtareaSerializer(subtarea)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = SubtareaSerializer(subtarea, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        subtarea.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Vista HOY — Agrupada (vencidas, hoy, próximas)
# ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def actividades_hoy(request):
    """
    Devuelve todas las actividades del usuario agrupadas en:
    - vencidas: subtareas con fecha_objetivo < hoy (no completadas)
    - hoy: subtareas con fecha_objetivo = hoy
    - proximas: subtareas con fecha_objetivo > hoy (próximos 7 días)

    Ordenamiento (regla base):
    1. Vencidas primero (las más antiguas primero)
    2. Hoy (por horas estimadas desc — prioriza lo más pesado)
    3. Próximas (por fecha_objetivo asc, luego horas desc)

    Desempate: si misma fecha y mismas horas → orden por título alfabético
    """
    hoy = datetime.now().date()
    proxima_semana = hoy + timedelta(days=7)
    user = request.user

    # Obtener todas las subtareas relevantes del usuario
    subtareas_qs = Subtarea.objects.filter(
        actividad__usuario=user
    ).select_related('actividad')

    # Vencidas: fecha_objetivo < hoy, no completadas
    vencidas = subtareas_qs.filter(
        fecha_objetivo__lt=hoy,
        completada=False
    ).order_by('fecha_objetivo', '-horas_estimadas', 'titulo')

    # Hoy: fecha_objetivo = hoy
    de_hoy = subtareas_qs.filter(
        fecha_objetivo=hoy
    ).order_by('-horas_estimadas', 'titulo')

    # Próximas: fecha_objetivo > hoy y <= próxima semana, no completadas
    proximas = subtareas_qs.filter(
        fecha_objetivo__gt=hoy,
        fecha_objetivo__lte=proxima_semana,
        completada=False
    ).order_by('fecha_objetivo', '-horas_estimadas', 'titulo')

    def serialize_subtarea_con_actividad(subtarea):
        return {
            'id': subtarea.id,
            'titulo': subtarea.titulo,
            'tipo': subtarea.tipo,
            'fecha_objetivo': subtarea.fecha_objetivo,
            'horas_estimadas': float(subtarea.horas_estimadas) if subtarea.horas_estimadas else 0,
            'completada': subtarea.completada,
            'orden': subtarea.orden,
            'actividad': {
                'id': subtarea.actividad.id,
                'titulo': subtarea.actividad.titulo,
                'tipo': subtarea.actividad.tipo,
                'fecha_entrega': subtarea.actividad.fecha_entrega,
            }
        }

    # También cargar actividades con fecha_entrega hoy (sin importar subtareas)
    actividades_hoy_qs = Actividad.objects.filter(
        usuario=user,
        fecha_entrega=hoy
    ).prefetch_related('subtareas')
    actividades_serializer = ActividadSerializer(actividades_hoy_qs, many=True)

    # Horas totales planificadas hoy
    horas_hoy = de_hoy.aggregate(
        total=Sum('horas_estimadas')
    )['total'] or 0

    return Response({
        'fecha': str(hoy),
        'horas_planificadas_hoy': float(horas_hoy),
        'vencidas': [serialize_subtarea_con_actividad(s) for s in vencidas],
        'hoy': [serialize_subtarea_con_actividad(s) for s in de_hoy],
        'proximas': [serialize_subtarea_con_actividad(s) for s in proximas],
        'actividades_hoy': actividades_serializer.data,
    })


# ──────────────────────────────────────────────
# US-07: Detección de conflicto por sobrecarga
# ──────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verificar_conflicto(request):
    """
    Verifica si reprogramar una subtarea a una fecha genera conflicto de sobrecarga.

    Recibe:
    - fecha: la fecha destino
    - horas_nuevas: horas de la subtarea a mover
    - subtarea_id (opcional): ID de la subtarea que se mueve (para excluirla del cálculo)

    Responde:
    - hay_conflicto: bool
    - horas_actuales: horas ya planificadas ese día
    - horas_con_nueva: horas que quedarían
    - limite: límite diario del usuario
    - mensaje: texto descriptivo
    - alternativas: opciones para resolver el conflicto
    """
    serializer = ConflictoCheckSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    fecha = serializer.validated_data['fecha']
    horas_nuevas = serializer.validated_data['horas_nuevas']
    subtarea_id = serializer.validated_data.get('subtarea_id')

    # Obtener perfil del usuario
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=request.user,
        defaults={'limite_diario_horas': 6.0}
    )
    limite = perfil.limite_diario_horas

    # Calcular horas ya planificadas para ese día
    subtareas_dia = Subtarea.objects.filter(
        actividad__usuario=request.user,
        fecha_objetivo=fecha,
        completada=False
    )

    # Si estamos moviendo una subtarea existente, excluirla del cálculo
    if subtarea_id:
        subtareas_dia = subtareas_dia.exclude(id=subtarea_id)

    horas_actuales = subtareas_dia.aggregate(
        total=Sum('horas_estimadas')
    )['total'] or Decimal('0')

    horas_con_nueva = horas_actuales + horas_nuevas
    hay_conflicto = horas_con_nueva > limite

    # Construir respuesta
    response_data = {
        'hay_conflicto': hay_conflicto,
        'horas_actuales': float(horas_actuales),
        'horas_con_nueva': float(horas_con_nueva),
        'limite': float(limite),
        'fecha': str(fecha),
    }

    if hay_conflicto:
        response_data['mensaje'] = (
            f"Quedarías con {float(horas_con_nueva)}h planificadas "
            f"(límite {float(limite)}h)"
        )
        response_data['alternativas'] = [
            {
                'accion': 'mover',
                'descripcion': 'Mover a otro día con menos carga',
                'icono': 'calendar'
            },
            {
                'accion': 'reducir',
                'descripcion': 'Reducir las horas estimadas de esta subtarea',
                'icono': 'clock'
            },
            {
                'accion': 'posponer',
                'descripcion': 'Posponer para más adelante',
                'icono': 'arrow-right'
            },
            {
                'accion': 'forzar',
                'descripcion': 'Guardar de todos modos (superando el límite)',
                'icono': 'alert-triangle'
            },
        ]
    else:
        response_data['mensaje'] = (
            f"Sin conflicto: {float(horas_con_nueva)}h de {float(limite)}h"
        )

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carga_diaria(request):
    """
    Devuelve la carga de horas planificadas por día para los próximos 14 días.
    Útil para mostrar al usuario qué días están más cargados.
    """
    hoy = datetime.now().date()
    fin = hoy + timedelta(days=14)

    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=request.user,
        defaults={'limite_diario_horas': 6.0}
    )

    # Obtener subtareas no completadas en el rango
    subtareas = Subtarea.objects.filter(
        actividad__usuario=request.user,
        fecha_objetivo__gte=hoy,
        fecha_objetivo__lte=fin,
        completada=False
    ).values('fecha_objetivo').annotate(
        total_horas=Sum('horas_estimadas')
    ).order_by('fecha_objetivo')

    carga_map = {str(s['fecha_objetivo']): float(s['total_horas']) for s in subtareas}

    dias = []
    current = hoy
    while current <= fin:
        horas = carga_map.get(str(current), 0)
        dias.append({
            'fecha': str(current),
            'horas_planificadas': horas,
            'limite': float(perfil.limite_diario_horas),
            'sobrecargado': horas > float(perfil.limite_diario_horas),
        })
        current += timedelta(days=1)

    return Response({
        'limite_diario': float(perfil.limite_diario_horas),
        'dias': dias
    })