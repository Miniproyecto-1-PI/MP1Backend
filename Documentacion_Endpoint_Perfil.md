# Documentación API - Endpoint Perfil de Usuario

## PUT /api/auth/perfil/

### Actualizar Perfil de Usuario

Este endpoint permite actualizar la configuración personalizada del usuario autenticado.

---

### Descripción General

| Campo | Descripción |
|-------|-------------|
| **Endpoint** | `PUT /api/auth/perfil/` |
| **Método** | PUT |
| **Autenticación** | JWT (Bearer Token) |
| **Tags** | Autenticación |

---

### Campos Editables

- **limite_diario_horas** (obligatorio): Límite máximo de horas que el usuario puede planificar por día.

  - Valor por defecto: 6.0 horas
  - Rango válido: 1.0 a 16.0 horas
  - Validación: El sistema no permitirá valores fuera de este rango.

---

### Uso Recomendado

| Rango de Horas | Uso Recomendado |
|---------------|----------------|
| 4-6 horas | Jornada estándar de productividad |
| 6-8 horas | Día completo de estudio/trabajo |
| 8+ horas | Días de alta demanda (exámenes, proyectos) |

---

### Request (Cuerpo de la Solicitud)

```json
{
  "limite_diario_horas": 8.0
}
```

### Response - Éxito (200)

```json
{
  "message": "Tu límite diario se actualizó a 4.0h",
  "limite_diario_horas": 4.0,
  "limite_anterior": 12.0
}
```

| Campo | Tipo | Descripción |
|-------|------|-----------|
| message | string | Mensaje de confirmación |
| limite_diario_horas | float | Nuevo límite configurado |
| limite_anterior | float | Límite anterior |

---

### Response - Error (400)

```json
{
  "limite_diario_horas": ["El mínimo es 1 hora por día. Así te aseguras de avanzar al menos un poco cada día."]
}
```

**Errores posibles:**

- `limite_diario_horas` menor a 1: "El mínimo es 1 hora por día. Así te aseguras de avanzar al menos un poco cada día."
- `limite_diario_horas` mayor a 16: "El máximo es 16 horas por día. Recuerda que también necesitas descansar."

---

### Calidad IxD: Opciones Comprensibles + Feedback

#### Mensajes de Feedback Claros

| Situación | Mensaje |
|----------|--------|
| Actualización exitosa | "Tu límite diario se actualizó a X.0h" |
| Sin conflicto | "Todo bien: tendrías Xh de Yh planificadas — sin conflicto" |
| Con conflicto | "Quedarías con Xh planificadas para ese día, pero tu límite es de Yh." |

#### Validación con Mensajes Explicativos

El sistema proporciona mensajes de error claros cuando el usuario ingresa un valor inválido:

- **Valor muy bajo** (menor a 1 hora):
  "El mínimo es 1 hora por día. Así te aseguras de avanzar al menos un poco cada día."

- **Valor muy alto** (mayor a 16 horas):
  "El máximo es 16 horas por día. Recuerda que también necesitas descansar."

---

### Flujo Claro: Opciones, Confirmación, Mensajes sin Jerga

#### Opción 1: Actualización de Límite

1. Usuario envía request con nuevo límite
2. Sistema valida el valor (1-16 horas)
3. Sistema retorna mensaje de confirmación con el nuevo valor y el valor anterior

#### Opción 2: Detección de Conflictos

El endpoint `/conflicto/verificar/` proporciona alternativas claras cuando hay conflicto:

```json
{
  "hay_conflicto": true,
  "horas_actuales": 6.0,
  "horas_con_nueva": 9.0,
  "horas_excedente": 3.0,
  "horas_disponibles": 0.0,
  "limite": 6.0,
  "mensaje": "Quedarías con 9.0h planificadas para ese día, pero tu límite es de 6.0h.",
  "alternativas": [
    {
      "accion": "mover",
      "titulo": "Elegir otro día",
      "descripcion": "Busca un día con menos carga para esta tarea"
    },
    {
      "accion": "reducir",
      "titulo": "Dedicarle menos tiempo",
      "descripcion": "Ajustar a 6.0h (el espacio que queda)"
    },
    {
      "accion": "posponer",
      "titulo": "Dejar para mañana",
      "descripcion": "Mover automáticamente al día siguiente"
    },
    {
      "accion": "forzar",
      "titulo": "Guardar de todos modos",
      "descripcion": "Acepto que será un día exigente"
    }
  ]
}
```

---

### Ejemplo de Uso

**Request:**
```
PUT /api/auth/perfil/
Content-Type: application/json
Authorization: Bearer <token>

{
  "limite_diario_horas": 8.0
}
```

**Response:**
```
{
  "message": "Tu límite diario se actualizó a 8.0h",
  "limite_diario_horas": 8.0,
  "limite_anterior": 6.0
}
```

---

### Resumen de Principios de Diseño Aplicados

| Principio | Implementación |
|----------|---------------|
| **Opciones comprensibles** | Valores de límite con recomendaciones claras (4-6h, 6-8h, 8+h) |
| **Feedback inmediato** | Mensaje de confirmación con valor nuevo y anterior |
| **Validación sin jerga** | Mensajes en lenguaje natural entendible |
| **Flujo claro** | Pasos simples: enviar → validar → confirmar |
| **Alternativas** | 4 opciones cuando hay conflicto (mover, reducir, posponer, forzar) |