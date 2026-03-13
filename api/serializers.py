from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import Actividad, Subtarea, PerfilUsuario


# ──────────────────────────────────────────────
# Auth Serializers
# ──────────────────────────────────────────────

class RegistroSerializer(serializers.ModelSerializer):
    """Serializer para registro de nuevos usuarios."""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name']

    def validate_username(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre de usuario es requerido")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso")
        return value.strip()

    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El correo electrónico es requerido")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado")
        return value.strip().lower()

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Las contraseñas no coinciden"
            })
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
        )
        # Crear perfil con límite diario por defecto
        PerfilUsuario.objects.create(usuario=user)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login — no revela si el usuario existe."""
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(
            username=data.get('username'),
            password=data.get('password')
        )
        if not user:
            # Mensaje genérico: no revela si el usuario existe
            raise serializers.ValidationError({
                "detail": "Credenciales inválidas"
            })
        if not user.is_active:
            raise serializers.ValidationError({
                "detail": "Credenciales inválidas"
            })
        data['user'] = user
        return data


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para devolver datos del usuario autenticado."""
    limite_diario_horas = serializers.DecimalField(
        source='perfil.limite_diario_horas',
        max_digits=4,
        decimal_places=1,
        read_only=True
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'limite_diario_horas']
        read_only_fields = ['id', 'username', 'email', 'first_name']


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para actualizar configuración del perfil."""
    class Meta:
        model = PerfilUsuario
        fields = ['limite_diario_horas']

    def validate_limite_diario_horas(self, value):
        if value <= 0:
            raise serializers.ValidationError("El límite debe ser mayor a 0")
        if value > 24:
            raise serializers.ValidationError("El límite no puede superar 24 horas")
        return value


# ──────────────────────────────────────────────
# Task Serializers
# ──────────────────────────────────────────────

class SubtareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtarea
        fields = ['id', 'titulo', 'tipo', 'fecha_objetivo', 'horas_estimadas', 'completada', 'orden', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_titulo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El título de la subtarea no puede estar vacío")
        return value.strip()

    def validate_horas_estimadas(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Las horas de la subtarea deben ser mayores a 0")
        return value


class ActividadSerializer(serializers.ModelSerializer):
    subtareas = SubtareaSerializer(many=True, required=False)

    class Meta:
        model = Actividad
        fields = ['id', 'titulo', 'descripcion', 'tipo', 'fecha_entrega', 'subtareas', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_titulo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El título de la actividad es requerido")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("El título debe tener al menos 3 caracteres")
        return value.strip()

    def validate_descripcion(self, value):
        if value and len(value.strip()) > 500:
            raise serializers.ValidationError("La descripción no puede exceder 500 caracteres")
        return value.strip() if value else ""

    def validate_fecha_entrega(self, value):
        if not value:
            raise serializers.ValidationError("La fecha de entrega es requerida")
        return value

    def validate_subtareas(self, value):
        if value:
            titulos = [s.get('titulo', '').strip() for s in value if s.get('titulo')]
            if len(titulos) != len(set(titulos)):
                raise serializers.ValidationError("No puede haber subtareas con títulos duplicados")
        return value

    def create(self, validated_data):
        subtareas_data = validated_data.pop('subtareas', [])
        actividad = Actividad.objects.create(**validated_data)

        for idx, subtarea_data in enumerate(subtareas_data):
            Subtarea.objects.create(
                actividad=actividad,
                orden=idx,
                **subtarea_data
            )

        return actividad

    def update(self, instance, validated_data):
        subtareas_data = validated_data.pop('subtareas', None)

        instance.titulo = validated_data.get('titulo', instance.titulo)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.tipo = validated_data.get('tipo', instance.tipo)
        instance.fecha_entrega = validated_data.get('fecha_entrega', instance.fecha_entrega)
        instance.save()

        if subtareas_data is not None:
            requests_subtareas = self.initial_data.get('subtareas', [])
            keep_subtareas_ids = []

            for idx, s_data in enumerate(requests_subtareas):
                subtarea_id = s_data.get('id')
                if subtarea_id:
                    try:
                        subtarea = Subtarea.objects.get(id=subtarea_id, actividad=instance)
                        subtarea.titulo = s_data.get('titulo', subtarea.titulo)
                        subtarea.tipo = s_data.get('tipo', subtarea.tipo)
                        if s_data.get('fecha_objetivo'):
                            subtarea.fecha_objetivo = s_data.get('fecha_objetivo')
                        if s_data.get('horas_estimadas'):
                            subtarea.horas_estimadas = s_data.get('horas_estimadas')
                        if 'completada' in s_data:
                            subtarea.completada = s_data['completada']
                        subtarea.orden = idx
                        subtarea.save()
                        keep_subtareas_ids.append(subtarea.id)
                    except Subtarea.DoesNotExist:
                        pass
                else:
                    new_subtarea = Subtarea.objects.create(
                        actividad=instance,
                        titulo=s_data.get('titulo', ''),
                        tipo=s_data.get('tipo', 'otro'),
                        fecha_objetivo=s_data.get('fecha_objetivo'),
                        horas_estimadas=s_data.get('horas_estimadas'),
                        completada=s_data.get('completada', False),
                        orden=idx
                    )
                    keep_subtareas_ids.append(new_subtarea.id)

            Subtarea.objects.filter(actividad=instance).exclude(id__in=keep_subtareas_ids).delete()

        return instance


# ──────────────────────────────────────────────
# Conflict Detection Serializer
# ──────────────────────────────────────────────

class ConflictoCheckSerializer(serializers.Serializer):
    """Serializer para verificar conflictos de sobrecarga diaria."""
    fecha = serializers.DateField()
    horas_nuevas = serializers.DecimalField(max_digits=5, decimal_places=2)
    subtarea_id = serializers.IntegerField(required=False, help_text="ID de subtarea a excluir del cálculo (si se reprograma)")
