# MP1Backend
Backend del Mini-proyecto 1: Planificador de Estudio

## 📖 Contexto del Proyecto
Los estudiantes universitarios necesitan planificar, ejecutar y reprogramar el trabajo asociado a **actividades evaluativas**, así como visualizar su progreso y prioridades sin fricción, especialmente cuando surgen imprevistos (cambios de fechas, acumulación de tareas, sobrecarga semanal).

Este repositorio contiene el backend de la aplicación web, construido con Django (Python), encargado de gestionar la lógica de negocio, persistencia de datos y exposición de APIs para el frontend.

### 🎯 Objetivos Principales de la Aplicación
La aplicación web permite:
1. **Crear actividades evaluativas** y establecer un plan de trabajo inicial.
2. **Registrar la ejecución** de tareas (avance real).
3. **Reprogramar** ante imprevistos, detectando y facilitando la resolución de conflictos de fechas.
4. **Visualizar el momento presente ("Hoy")**, mostrando de inmediato el progreso y las prioridades del día bajo criterios comprensibles.

## 🛠️ Stack Tecnológico (Backend)
- **Django** (Framework web de Python)
- **Python 3.x**
- **SQLite** (Base de datos por defecto)
- **python-dotenv** (Gestión de variables de entorno)

## 🚀 Configuración e Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/Miniproyecto-1-PI/MP1Backend.git
cd MP1Backend
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows
# .\.venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Copiar `.env.example` y renombrarlo a `.env`, ajustando los valores según sea necesario.

### 5. Ejecutar migraciones
```bash
python manage.py migrate
```

### 6. Iniciar servidor
```bash
python manage.py runserver
```

## 🔗 Repositorios Relacionados
- Frontend: [MP1Frontend](https://github.com/Miniproyecto-1-PI/MP1Frontend.git)