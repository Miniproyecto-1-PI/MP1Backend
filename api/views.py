from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from decimal import Decimal

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.serializers import Serializer, CharField, FloatField
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, inline_serializer

from .models import Actividad, Subtarea, PerfilUsuario
from .serializers import (
    ActividadSerializer,
    SubtareaSerializer,
    RegistroSerializer,
    LoginSerializer,
    UsuarioSerializer,
    PerfilUsuarioSerializer,
    ConflictoCheckSerializer,
    SubtareaStatusSerializer,
    ActividadProgresoSerializer,
)


def test_endpoint(request):
    return JsonResponse({
        "message": "API funcionando correctamente 🚀"
    })


# ──────────────────────────────────────────────
# Auth Views
# ──────────────────────────────────────────────

@extend_schema(
    request=RegistroSerializer,
    responses={
        201: OpenApiResponse(description='Usuario creado exitosamente'),
        400: OpenApiResponse(description='Datos inválidos'),
    },
    description='Registrar un nuevo usuario en el sistema.'
)
@api_view(['POST'])
@permission_classes([AllowAny])
def registro_view(request):
    serializer = RegistroSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Cuenta creada exitosamente',
            'user': {
                'id': user.id,
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


@extend_schema(
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(description='Login exitoso'),
        400: OpenApiResponse(description='Credenciales inválidas'),
    },
    description='Iniciar sesión y obtener tokens JWT.'
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
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


@extend_schema(
    responses={200: UsuarioSerializer},
    description='Obtener datos del usuario autenticado actual.'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=user,
        defaults={'limite_diario_horas': 6.0}
    )
    return Response({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'limite_diario_horas': float(perfil.limite_diario_horas),
    })


@extend_schema(
    request=PerfilUsuarioSerializer,
    responses={
        200: inline_serializer(
            name='PerfilResponse',
            fields={
                'message': CharField(),
                'limite_diario_horas': FloatField(),
                'limite_anterior': FloatField(),
            },
        ),
        400: OpenApiResponse(
            description='Datos inválidos - el límite debe estar entre 1 y 16 horas',
        ),
    },
    description='''
## Actualizar Perfil de Usuario

Este endpoint permite actualizar la configuración personalizada del usuario autenticado.

### Campos editables:
- **limite_diario_horas** (obligatorio): Límite máximo de horas que el usuario puede planificar por día.
  - Valor por defecto: 6.0 horas
  - Rango válido: 1.0 a 16.0 horas
  - Validación: El sistema no permitirá valores fuera de este rango.

### Uso recomendado:
- **4-6 horas**: Jornada estándar de productividad
- **6-8 horas**: Día completo de estudio/trabajo
- **8+ horas**: Días de alta demanda (exámenes, proyectos)

### Respuesta exitosa:
Devuelve el nuevo límite configurado junto con el límite anterior para referencia.''',
    summary='Actualizar Perfil de Usuario',
    tags=['Autenticación'],
    examples=[
        OpenApiExample(
            name='Respuesta exitosa',
            description='Ejemplo de respuesta cuando el límite se actualiza correctamente',
            value={
                "message": "Tu límite diario se actualizó a 4.0h",
                "limite_diario_horas": 4.0,
                "limite_anterior": 12.0
            },
        ),
    ]
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_perfil_view(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=request.user,
        defaults={'limite_diario_horas': 6.0}
    )
    limite_anterior = float(perfil.limite_diario_horas)
    serializer = PerfilUsuarioSerializer(perfil, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        perfil.refresh_from_db()
        nuevo_limite = float(perfil.limite_diario_horas)
        return Response({
            'message': f'Tu límite diario se actualizó a {nuevo_limite}h',
            'limite_diario_horas': nuevo_limite,
            'limite_anterior': limite_anterior,
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Actividades — CRUD protegido por usuario
# ──────────────────────────────────────────────

@extend_schema(
    summary='CRUD de Actividades',
    description='Gestionar actividades del usuario. Solo devuelve actividades propias del usuario autenticado.',
    responses={
        200: ActividadSerializer(many=True),
        201: ActividadSerializer,
        204: None,
    }
)
class ActividadViewSet(viewsets.ModelViewSet):
    serializer_class = ActividadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Actividad.objects.filter(
            usuario=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


# ──────────────────────────────────────────────
# Subtareas — CRUD protegido por usuario
# ──────────────────────────────────────────────

@extend_schema(
    summary='Listar/Crear Subtareas',
    description='Lista las subtareas de una actividad o crea una nueva.',
    parameters=[
        {
            'name': 'actividad_id',
            'in': 'path',
            'required': True,
            'schema': {'type': 'integer'},
            'description': 'ID de la actividad padre'
        }
    ],
    responses={
        200: SubtareaSerializer(many=True),
        201: SubtareaSerializer,
        404: OpenApiResponse(description='Actividad no encontrada'),
    }
)
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


@extend_schema(
    summary='Detalle de Subtarea',
    description='Obtener, actualizar o eliminar una subtarea específica.',
    parameters=[
        {
            'name': 'pk',
            'in': 'path',
            'required': True,
            'schema': {'type': 'integer'},
            'description': 'ID de la subtarea'
        }
    ],
    responses={
        200: SubtareaSerializer,
        204: None,
        404: OpenApiResponse(description='Subtarea no encontrada'),
    }
)
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

@extend_schema(
    summary='Actividades de Hoy',
    description='''Devuelve todas las actividades del usuario agrupadas en:
- **vencidas**: subtareas con fecha_objetivo < hoy (no completadas)
- **hoy**: subtareas con fecha_objetivo = hoy
- **proximas**: subtareas con fecha_objetivo > hoy (próximos 7 días)

Ordenamiento:
1. Vencidas primero (las más antiguas primero)
2. Hoy (por horas estimadas desc — prioriza lo más pesado)
3. Próximas (por fecha_objetivo asc, luego horas desc)''',
    responses={
        200: OpenApiResponse(description='Datos del día agrupados'),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def actividades_hoy(request):
    hoy = timezone.localdate()
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
            'estado': subtarea.estado,
            'nota': subtarea.nota,
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

    # Novedad: Actividades que no tienen ninguna subtarea planificada
    # Para que el usuario las pueda ver y gestionar, independientemente de su fecha_entrega.
    actividades_sin_planificar_qs = Actividad.objects.filter(
        usuario=user,
        subtareas__isnull=True
    ).exclude(
        fecha_entrega=hoy # excluir las que ya salen en actividades_hoy
    )
    actividades_sin_planificar_serializer = ActividadSerializer(actividades_sin_planificar_qs, many=True)

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
        'todas': [serialize_subtarea_con_actividad(s) for s in subtareas_qs.order_by('-id')],
        'actividades_hoy': actividades_serializer.data,
        'actividades_sin_planificar': actividades_sin_planificar_serializer.data,
    })


# ──────────────────────────────────────────────
# US-07: Detección de conflicto por sobrecarga
# ──────────────────────────────────────────────

@extend_schema(
    summary='Verificar Conflicto de Carga',
    description='''Verifica si reprogramar una subtarea a una fecha genera conflicto de sobrecarga.

Recibe:
- fecha: la fecha destino
- horas_nuevas: horas de la subtarea a mover
- subtarea_id (opcional): ID de la subtarea que se mueve (para excluirla del cálculo)

Responde con información de conflicto y alternativas.''',
    request=ConflictoCheckSerializer,
    responses={
        200: OpenApiResponse(description='Resultado de la verificación'),
        400: OpenApiResponse(description='Datos inválidos'),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verificar_conflicto(request):
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
    horas_excedente = float(horas_con_nueva - limite) if hay_conflicto else 0
    horas_disponibles = max(0, float(limite - horas_actuales))

    response_data = {
        'hay_conflicto': hay_conflicto,
        'horas_actuales': float(horas_actuales),
        'horas_con_nueva': float(horas_con_nueva),
        'horas_excedente': horas_excedente,
        'horas_disponibles': horas_disponibles,
        'limite': float(limite),
        'fecha': str(fecha),
        'porcentaje_uso': min(100, round(float(horas_con_nueva / limite) * 100)) if limite > 0 else 100,
    }

    if hay_conflicto:
        response_data['mensaje'] = (
            f"Quedarías con {float(horas_con_nueva)}h planificadas para ese día, "
            f"pero tu límite es de {float(limite)}h."
        )
        response_data['mensaje_corto'] = (
            f"{float(horas_con_nueva)}h de {float(limite)}h — "
            f"excedes por {horas_excedente:.1f}h"
        )
        response_data['alternativas'] = [
            {
                'accion': 'mover',
                'titulo': 'Elegir otro día',
                'descripcion': 'Busca un día con menos carga para esta tarea',
                'icono': 'calendar'
            },
            {
                'accion': 'reducir',
                'titulo': 'Dedicarle menos tiempo',
                'descripcion': f'Ajustar a {horas_disponibles:.1f}h (el espacio que queda)',
                'icono': 'clock'
            },
            {
                'accion': 'posponer',
                'titulo': 'Dejar para mañana',
                'descripcion': 'Mover automáticamente al día siguiente',
                'icono': 'arrow-right'
            },
            {
                'accion': 'forzar',
                'titulo': 'Guardar de todos modos',
                'descripcion': 'Acepto que será un día exigente',
                'icono': 'alert-triangle'
            },
        ]
    else:
        response_data['mensaje'] = (
            f"Todo bien: tendrías {float(horas_con_nueva)}h de {float(limite)}h planificadas"
        )
        response_data['mensaje_corto'] = (
            f"{float(horas_con_nueva)}h de {float(limite)}h — sin conflicto"
        )

    return Response(response_data)


@extend_schema(
    summary='Carga Diaria (Próximos 14 días)',
    description='Devuelve la carga de horas planificadas por día para los próximos 14 días. Útil para mostrar qué días están más cargados.',
    responses={
        200: OpenApiResponse(description='Carga diaria por día'),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carga_diaria(request):
    hoy = timezone.localdate()
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


# ──────────────────────────────────────────────
# US-09: Registrar avance de subtarea
# ──────────────────────────────────────────────

@extend_schema(
    summary='Actualizar Estado de Subtarea',
    description='''## Registrar avance de una subtarea (US-09)

Permite marcar una subtarea como **hecha** o **pospuesta**, con una nota opcional.

### Estados válidos:
- `"done"` → La subtarea se marca como hecha (completada = true)
- `"postponed"` → La subtarea se marca como pospuesta (completada = false)

### Nota opcional:
Se puede incluir una nota al posponer. La nota se guarda junto con el estado.

### Ejemplo de uso:
```json
{ "status": "done" }
```

```json
{ "status": "postponed", "note": "Falta revisar el último capítulo" }
```''',
    request=SubtareaStatusSerializer,
    responses={
        200: SubtareaSerializer,
        400: OpenApiResponse(description='Estado inválido — debe ser "done" o "postponed"'),
        404: OpenApiResponse(description='Subtarea no encontrada o no pertenece al usuario'),
    },
    tags=['Subtareas'],
    examples=[
        OpenApiExample(
            name='Marcar como hecha',
            description='Marcar una subtarea como completada',
            value={"status": "done"},
            request_only=True,
        ),
        OpenApiExample(
            name='Posponer con nota',
            description='Posponer una subtarea con una nota opcional',
            value={"status": "postponed", "note": "Falta revisar el último capítulo"},
            request_only=True,
        ),
        OpenApiExample(
            name='Respuesta exitosa',
            description='Subtarea actualizada',
            value={
                "id": 1,
                "titulo": "Leer capítulo 5",
                "tipo": "estudio",
                "fecha_objetivo": "2026-05-07",
                "horas_estimadas": 2.0,
                "completada": True,
                "estado": "hecha",
                "nota": "",
                "orden": 0,
                "created_at": "2026-05-01T10:00:00Z"
            },
            response_only=True,
        ),
    ]
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def subtarea_update_status(request, pk):
    try:
        subtarea = Subtarea.objects.get(pk=pk, actividad__usuario=request.user)
    except Subtarea.DoesNotExist:
        return Response(
            {"detail": "Subtarea no encontrada"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = SubtareaStatusSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    new_status = serializer.validated_data['status']
    note = serializer.validated_data.get('note', '')

    if new_status == 'done':
        subtarea.estado = 'hecha'
        subtarea.completada = True
        subtarea.nota = note
    elif new_status == 'postponed':
        subtarea.estado = 'pospuesta'
        subtarea.completada = False
        subtarea.nota = note
    elif new_status == 'pending':
        subtarea.estado = 'pendiente'
        subtarea.completada = False
        subtarea.nota = note

    try:
        subtarea.save()
    except Exception:
        return Response(
            {"detail": "Error interno al guardar el estado"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(SubtareaSerializer(subtarea).data)


# ──────────────────────────────────────────────
# US-10: Progreso por actividad
# ──────────────────────────────────────────────

@extend_schema(
    summary='Progreso de Actividad',
    description='''## Ver progreso por actividad (US-10)

Calcula el progreso de una actividad basándose en los estados de sus subtareas.

### Cálculo:
- **done**: Subtareas con estado "hecha"
- **postponed**: Subtareas con estado "pospuesta"
- **pending**: Subtareas con estado "pendiente"
- **total**: Número total de subtareas
- **percentage**: `(done / total) * 100`, redondeado a 1 decimal

### Ejemplo de respuesta:
```json
{
  "done": 3,
  "postponed": 1,
  "pending": 2,
  "total": 6,
  "percentage": 50.0
}
```''',
    responses={
        200: ActividadProgresoSerializer,
        404: OpenApiResponse(description='Actividad no encontrada o no pertenece al usuario'),
    },
    tags=['Actividades'],
    examples=[
        OpenApiExample(
            name='Progreso parcial',
            description='Actividad con progreso parcial',
            value={
                "done": 3,
                "postponed": 1,
                "pending": 2,
                "total": 6,
                "percentage": 50.0
            },
            response_only=True,
        ),
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def actividad_progreso(request, actividad_id):
    try:
        actividad = Actividad.objects.get(pk=actividad_id, usuario=request.user)
    except Actividad.DoesNotExist:
        return Response(
            {"detail": "Actividad no encontrada"},
            status=status.HTTP_404_NOT_FOUND
        )

    subtareas = actividad.subtareas.all()
    total = subtareas.count()
    done = subtareas.filter(estado='hecha').count()
    postponed = subtareas.filter(estado='pospuesta').count()
    pending = subtareas.filter(estado='pendiente').count()
    percentage = round((done / total) * 100, 1) if total > 0 else 0

    return Response({
        'done': done,
        'postponed': postponed,
        'pending': pending,
        'total': total,
        'percentage': percentage,
    })