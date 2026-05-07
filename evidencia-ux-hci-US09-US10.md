# Evidencia UX/HCI — US-09 & US-10

**Sprint:** T4
**Fecha:** 2026-05-06
**Autor(es):** Equipo de desarrollo

---

## 1. Decisiones de diseño de interacción

### 1.1 Registro de avance (US-09)

**Decisión:** Usar botones de acción directa ("Hecha" / "Posponer") en lugar de un menú desplegable.

**Justificación HCI:**
- Principio de visibilidad (Nielsen #1): las acciones principales deben estar siempre visibles, sin pasos intermedios.
- Reducción de carga cognitiva: el usuario no tiene que buscar la acción en un menú.
- Consistencia con patrones móviles comunes (swipe-to-complete / tap-to-done).

**Alternativa descartada:** Menú contextual con opciones múltiples — descartado porque añade un paso innecesario para la acción más frecuente.

---

### 1.2 Nota opcional al posponer

**Decisión:** La nota se muestra solo cuando el usuario selecciona "Posponer" (campo condicional).

**Justificación HCI:**
- Principio de diseño progresivo: no mostrar campos que no aplican al estado actual.
- Evitar sobrecarga de información en pantalla.
- El campo es opcional y su ausencia no bloquea la acción.

**Alternativa descartada:** Mostrar el campo de nota siempre — descartado porque genera ruido visual y puede confundir sobre si la nota es requerida.

---

### 1.3 Indicador de progreso (US-10)

**Decisión:** Mostrar progreso como `N/Total completadas` + barra visual de porcentaje.

**Justificación HCI:**
- Doble codificación (texto + visual): facilita la comprensión rápida sin depender solo del color.
- Accesibilidad: el conteo numérico es legible por lectores de pantalla.
- El porcentaje da contexto inmediato de "cuánto falta" sin cálculo mental.

**Alternativa descartada:** Solo barra de progreso sin número — descartado por ambigüedad en estados intermedios (¿50% = 2/4 o 5/10?).

---

## 2. Microcopy — Decisiones de redacción

| Situación | Texto elegido | Razón |
|-----------|---------------|-------|
| Estado vacío | "Aún no hay subtareas registradas" | Claro, no culpa al usuario, orientado a acción futura |
| Confirmación hecha | "Subtarea marcada como hecha ✓" | Breve, positivo, con refuerzo visual |
| Confirmación pospuesta | "Subtarea pospuesta" | Neutral, sin juicio |
| Error al guardar | "No se pudo guardar. Intenta de nuevo" | Directo, indica acción a tomar |
| Sin progreso | "0 de N completadas" | Evita el "0%" que puede sentirse negativo |

**Principio aplicado:** Microcopy orientado a acción (Nielsen #9 — ayuda al usuario a reconocer, diagnosticar y recuperarse de errores).

---

## 3. Consistencia con /hoy

**Decisión:** Los estados "Hecha" y "Pospuesta" se reflejan en la vista `/hoy` usando los mismos iconos y colores que en la vista de actividad.

**Justificación HCI:**
- Principio de consistencia (Nielsen #4): el mismo estado no puede verse diferente en dos vistas.
- Reduce el tiempo de aprendizaje: el usuario asocia color/ícono con estado sin re-aprender.

**Implementación:**
- ✅ Verde / ícono check = Hecha
- ⏸ Gris / ícono pausa = Pospuesta
- ⬜ Sin color / vacío = Pendiente

---

## 4. Capturas de pantalla

> _(Insertar capturas aquí durante la implementación)_

- [ ] Captura: botones de acción en subtarea (Hecha / Posponer)
- [ ] Captura: campo de nota al posponer
- [ ] Captura: indicador de progreso en actividad
- [ ] Captura: mensajes de estado (error, confirmación, vacío)
- [ ] Captura: vista `/hoy` con estados reflejados
- [ ] Captura: vista `/progreso` con dashboard de avance

---

## 5. Link a Swagger

> Documentación API disponible en: `http://localhost:8000/api/docs/`
>
> Endpoints documentados:
> - `PATCH /api/subtareas/{id}/status/` — Actualizar estado de subtarea
> - `GET /api/actividades/{id}/progreso/` — Consultar progreso de actividad

---

## 6. Checklist de criterios

- [x] C1: Estado persiste tras recargar página (PATCH guarda en BD, GET devuelve estado)
- [x] C2: Progreso calculado consistentemente (done/total * 100)
- [x] C3: Vista /hoy refleja cambios de estado (badges con mismos iconos/colores)
- [x] C4: Microcopy presente en todos los estados
- [x] C5: Swagger actualizado con ambos endpoints (drf-spectacular con ejemplos)
- [x] C6: Este documento completo con decisiones UX/HCI
