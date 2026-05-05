# 1. Usamos una imagen ligera de Python como base
FROM python:3.11-slim

# 2. Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiamos el archivo de requerimientos e instalamos las librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos tu script de sincronización al contenedor
COPY sync.py .

# 5. Creamos la carpeta que el script va a vigilar
RUN mkdir -p /app/mi_nube

# 6. Comando para arrancar el script cuando el contenedor inicie
CMD ["python", "sync.py"]