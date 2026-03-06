from django.db import models
from django.contrib.auth.models import User


class Actividad(models.Model):
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    fecha_entrega = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo


class Subtarea(models.Model):
    actividad = models.ForeignKey(
        Actividad, 
        on_delete=models.CASCADE, 
        related_name='subtareas'
    )
    titulo = models.CharField(max_length=255)
    fecha_objetivo = models.DateField(null=True, blank=True)
    horas_estimadas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completada = models.BooleanField(default=False)
    orden = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.actividad.titulo})"
