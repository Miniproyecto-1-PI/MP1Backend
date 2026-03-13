# MP1Backend

# Setup Instructions

## 1. Clonar repo
git clone ...

## 2. Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\activate

## 3. Instalar dependencias
pip install -r requirements.txt

## 4. Crear archivo .env
Copiar .env.example y renombrarlo a .env

## 5. Ejecutar migraciones
python manage.py migrate

## 6. Run server
python manage.py runserver