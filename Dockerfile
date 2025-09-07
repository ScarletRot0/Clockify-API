# Imagen base oficial de Python
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Copiar los archivos
COPY . /app

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto
EXPOSE 8080

# Comando dinámico dependiendo del entorno
CMD ["sh", "-c", "if [ \"$FLASK_ENV\" = \"development\" ]; then python run.py; else gunicorn -b 0.0.0.0:8080 'app:create_app()' --workers=1 --timeout=60; fi"]
