from rest_framework import serializers
from django.utils import timezone
from .models import Actividad, Subtarea


class SubtareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtarea
        fields = ['id', 'titulo', 'fecha_objetivo', 'horas_estimadas', 'completada', 'orden', 'created_at']
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

    def update(self, instance, validated_data):
        subtareas_data = validated_data.pop('subtareas', None)
        
        instance.titulo = validated_data.get('titulo', instance.titulo)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.fecha_entrega = validated_data.get('fecha_entrega', instance.fecha_entrega)
        instance.save()
        
        if subtareas_data is not None:
            # Recreate all logic or use initial_data logic
            # Easiest way to "update" subtasks while preserving order is to map by title
            requests_subtareas = self.initial_data.get('subtareas', [])
            keep_subtareas_ids = []
            
            for idx, s_data in enumerate(requests_subtareas):
                subtarea_id = s_data.get('id')
                if subtarea_id:
                    try:
                        subtarea = Subtarea.objects.get(id=subtarea_id, actividad=instance)
                        subtarea.titulo = s_data.get('titulo', subtarea.titulo)
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
                        fecha_objetivo=s_data.get('fecha_objetivo'),
                        horas_estimadas=s_data.get('horas_estimadas'),
                        completada=s_data.get('completada', False),
                        orden=idx
                    )
                    keep_subtareas_ids.append(new_subtarea.id)
            
            Subtarea.objects.filter(actividad=instance).exclude(id__in=keep_subtareas_ids).delete()
            
        return instance
