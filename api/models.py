from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    """Perfil extendido del usuario con configuraciones personales."""
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    limite_diario_horas = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=6.0,
        help_text="Límite máximo de horas planificadas por día"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


TIPO_ACTIVIDAD_CHOICES = [
    ('tarea', 'Tarea'),
    ('proyecto', 'Proyecto'),
    ('examen', 'Examen'),
    ('quiz', 'Quiz'),
    ('laboratorio', 'Laboratorio'),
    ('lectura', 'Lectura'),
    ('otro', 'Otro'),
]

TIPO_SUBTAREA_CHOICES = [
    ('investigacion', 'Investigación'),
    ('redaccion', 'Redacción'),
    ('programacion', 'Programación'),
    ('estudio', 'Estudio'),
    ('revision', 'Revisión'),
    ('practica', 'Práctica'),
    ('otro', 'Otro'),
]


class Actividad(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='actividades',
        null=True,
        blank=True
    )
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_ACTIVIDAD_CHOICES,
        default='tarea'
    )
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
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_SUBTAREA_CHOICES,
        default='otro'
    )
    fecha_objetivo = models.DateField(null=True, blank=True)
    horas_estimadas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completada = models.BooleanField(default=False)
    orden = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.actividad.titulo})"
