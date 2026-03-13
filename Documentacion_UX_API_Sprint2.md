# Documentación Completa: Decisiones UX, Estados y API "Hoy"

A continuación, se presenta la documentación detallada estructurada según el formato solicitado, cubriendo las heurísticas de la plataforma implementadas en el último sprint.

---

## 1. Decisiones de Diseño (UX / HCI)

### Decisión 1: Prevención de Muerte Temprana y Ansiedad en la Espera (Manejo de Estados de Carga)
**Criterio UX (Heurística de Nielsen):**
"Visibilidad del estado del sistema". El sistema siempre debe mantener informado al usuario sobre lo que está ocurriendo, brindando un contexto claro durante las operaciones que toman tiempo de red.

**Evidencia / Aplicación:**
En la vista maestra “Hoy” (`/hoy`), se implementó un flujo visual durante la petición a la API. Al cargar la página, en lugar de mostrar una pantalla en blanco que pueda generar la percepción de una plataforma "caída", el sistema despliega inmediatamente el encabezado contextual (*Header*) acompañado de un indicador visual de procesamiento circular continuo (Loader2) y un mensaje textual explícito: *"Cargando tus actividades..."*. De este modo, la carga cognitiva se reduce, mitigando la ansiedad del estudiante.

### Decisión 2: Prevención de Errores Activa y Resolución In-Situ de Conflictos de Sobrecarga (US-07)
**Criterio UX (Heurística de Nielsen):**
"Prevención de errores" y "Ayuda a los usuarios a reconocer, diagnosticar y recuperarse de los errores". Es mucho mejor un buen diseño que prevenga que el problema de sobrecarga ocurra en absoluto, pero cuando ocurre, se debe proveer una salida clara y accionable, nunca un callejón sin salida.

**Evidencia / Aplicación:**
Cuando el usuario intenta reprogramar las horas de una subtarea y el sistema detecta que se superará el límite diario permitido (ej. 8 horas planificadas frente al límite de 6 horas), el sistema no bloquea pasivamente la acción mediante un simple "Error 400".
En su lugar, la interfaz de detalles de la actividad abre un modal descriptivo no técnico (*"Quedarías con 8h planificadas (límite 6h)"*) y le otorga el control absoluto a través de cuatro opciones de resolución de un solo clic:
- *Mover a otro día*
- *Reducir horas estimadas*
- *Posponer*
- *Guardar de todos modos (forzar)*

### Decisión 3: Seguridad Privada Discreta en el Acceso y Reconocimiento Acelerado de Tareas
**Criterio UX (Heurística de Nielsen):**
"Reconocer en lugar de recordar" (aplicado al front-end) y Arquitectura defensiva de la información.

**Evidencia / Aplicación:**
- **Autenticación (Seguridad):** Al momento de fallar el inicio de sesión, el front-end neutraliza la respuesta detallada de la API consolidando toda vulnerabilidad en un mensaje genérico *"La contraseña o el usuario son incorrectos"*. Esto previene que terceros malintencionados usen la plataforma como oráculo para confirmar si un correo existe.
- **Etiquetas Contextuales (Badges):** En la lista masiva de `HoyPage`, cada tarea despliega una insignia visual atenuada con la tipología ("Proyecto", "Examen", "Programación"). Minimizamos la memoria dependiente del usuario; en lugar de recordar a qué actividad grande pertenece una subtarea, el color y etiqueta lo exponen visualmente de golpe.

---

## 2. Iteraciones de la Vista "Hoy"

| Iteración / Fecha | Hallazgo (Problema Identificado) | Cambio Aplicado (Solución HCI) | Verificación (Resultado Final) |
| :--- | :--- | :--- | :--- |
| **Iteración 1:** (Sprint Actual) | Los estudiantes se sentían abrumados al ver todas las tareas del mes en una sola lista sin jerarquía real de acción inmediata. | Se construyó una vista agrupada (`/hoy`) que divide visualmente las responsabilidades en 3 bloques secuenciales: **Vencidas**, **Hoy** y **Próximas**; imponiendo un ordenamiento estricto priorizando el atraso, luego el peso operativo (horas estimadas) y el desempate alfabético. | El esfuerzo visual se enfoca en resolver primero la alerta crítica ("Vencidas"), y dentro de estas, la más laboriosa; el estudiante consume las tareas cronológicamente reduciendo la fatiga de elección. |
| **Iteración 2:** (Sprint Actual) | La lógica detrás de por qué una tarea aparecía antes que otra dentro del mismo grupo era invisible para el usuario («Caja Negra»). | Se añadió una caja instruccional liviana (Regla de priorización) perpetuamente visible bajo el título de la vista, detallando textualmente las 3 reglas y el desempate alfabético aplicados a los bloques de datos. | Se mejoró la transparencia del sistema. El estudiante confía en el algoritmo de agrupamiento al poder deducirlo por lectura simple. |

---

## 3. Estados UX Consensuados en `/hoy`

Para abordar la variabilidad en los datos de la cuenta (Usuario con muchas tareas vs Usuario nuevo), se implementaron los siguientes estados del componente:

- **1. Estado de Éxito y Regla Base (Categorización):** Al haber datos, se pintan 3 bloques. El bloque de *Vencidas* se enmarca con bordes e íconos rojos que alertan su urgencia sin ser puramente agresivos (con fondo tenue). El bloque de *Próximas* reduce su opacidad en un 20% para restarle urgencia focal y no robar atención de los elementos vigentes.
- **2. Estado Vacío (Empty State Positivo):** Si el servidor retorna listas vacías, la página despliega un icono de verificación `CheckCircle2` ilustrando "Misión cumplida" junto al texto: *"No hay tareas pendientes. ¡Estás al día! Crea una nueva actividad para comenzar"*. Añade un botón de "Crear" guiando el flujo proactivo del sistema.
- **3. Estado de Error Perdonable:** En una falla de servidor (`500`) o fallo de CORS, el layout principal se mantiene íntegro. El bloque de error se envuelve en una caja delimitada, explica `"Error al cargar las actividades"` y muestra un botón de `Reintentar` hipervinculado, invitando al usuario a volver a conectarse sin forzar el reinicio manual con el botón de su explorador.

---

## 4. API Documentada (Request/Response Endpoints Nuevos)

A continuación, la estructura de la comunicación Cliente-Servidor de los 2 endpoints clave.

### Endpoint 1: Extracción y Agrupamiento "Hoy"
Devuelve las subtareas catalogadas según regla y filtradas estrictamente para el *usuario poseedor del token (Aislamiento)*.

| Propiedad | Valor |
|---------|---------|
| **Ruta** | `GET /api/actividades/hoy/` |
| **Headers** | `Authorization: Bearer <token_jwt>` |
| **Protección** | Restringido (`IsAuthenticated`) a nivel de vista Django. |

**Response Exitoso (200 OK):**
```json
{
  "fecha": "2026-03-12",
  "horas_planificadas_hoy": 6.0,
  "vencidas": [
    {
      "id": 14,
      "titulo": "Implementar base de datos",
      "tipo": "programacion",
      "fecha_objetivo": "2026-03-09",
      "horas_estimadas": 4.0,
      "completada": false,
      "actividad": { "id": 5, "titulo": "Proyecto de Software", "tipo": "proyecto" }
    }
  ],
  "hoy": [
    {
      "id": 17,
      "titulo": "Armar presentación oral",
      "tipo": "otro",
      "fecha_objetivo": "2026-03-12",
      "horas_estimadas": 3.0,
      "completada": false
    },
    {
      "id": 15,
      "titulo": "Programar API externa",
      "tipo": "programacion",
      "fecha_objetivo": "2026-03-12",
      "horas_estimadas": 3.0,
      "completada": false
    }
  ],
  "proximas": []
}
```
*(Nota de validación: En el bloque `"hoy"` el sistema envió "Armar" primero que "Programar", probando que el desempate alfabético funciona cuando ambas comparten la misma fecha de hoy y las mismas 3.0 horas estimadas).*

### Endpoint 2: Detección de Conflicto de Sobrecarga Diaria (US-07)
Validación en crudo requerida cuando se manipulan los metadatos de fechas y horas en los formularios del portal.

| Propiedad | Valor |
|---------|---------|
| **Ruta** | `POST /api/conflicto/verificar/` |
| **Headers** | `Authorization: Bearer <token_jwt>`, `Content-Type: application/json` |

**Payload de Entrada (Body Request):**
```json
{
  "fecha": "2026-03-12",
  "horas_nuevas": 3.0,
  "subtarea_id": 19
}
```

**Response Exitoso (200 OK) — "Conflicto Positivo":**
```json
{
  "hay_conflicto": true,
  "horas_actuales": 5.0,
  "horas_con_nueva": 8.0,
  "limite": 6.0,
  "fecha": "2026-03-12",
  "mensaje": "Quedarías con 8.0h planificadas (límite 6.0h)",
  "alternativas": [
    { "accion": "mover", "descripcion": "Mover a otro día con menos carga", "icono": "calendar" },
    { "accion": "reducir", "descripcion": "Reducir las horas estimadas de esta subtarea", "icono": "clock" },
    { "accion": "posponer", "descripcion": "Posponer para más adelante", "icono": "arrow-right" },
    { "accion": "forzar", "descripcion": "Guardar de todos modos (superando el límite)", "icono": "alert-triangle" }
  ]
}
```
*(Si no hubiese conflicto visualizado, el campo lógico `"hay_conflicto"` retornaría en valor `false` sin pintar arreglos de alternativas).*
