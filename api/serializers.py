from rest_framework import serializers
from .models import Actividad, Subtarea


class SubtareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtarea
        fields = ['id', 'titulo', 'completada', 'orden', 'created_at']
        read_only_fields = ['id', 'created_at']


class ActividadSerializer(serializers.ModelSerializer):
    subtareas = SubtareaSerializer(many=True, required=False)
    
    class Meta:
        model = Actividad
        fields = ['id', 'titulo', 'descripcion', 'fecha_entrega', 'subtareas', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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
