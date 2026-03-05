from rest_framework import serializers
from django.utils import timezone
from .models import Actividad, Subtarea


class SubtareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtarea
        fields = ['id', 'titulo', 'completada', 'orden', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_titulo(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El título de la subtarea no puede estar vacío")
        return value.strip()


class ActividadSerializer(serializers.ModelSerializer):
    subtareas = SubtareaSerializer(many=True, required=False)
    
    class Meta:
        model = Actividad
        fields = ['id', 'titulo', 'descripcion', 'fecha_entrega', 'subtareas', 'created_at', 'updated_at']
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
