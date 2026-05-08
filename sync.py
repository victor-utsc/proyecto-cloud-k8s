import os
import time
import boto3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURACIÓN SEGURA ---
# Python buscará estas variables en el entorno del contenedor, no en el texto.
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = 'sync-archivos-victor'
CARPETA_A_VIGILAR = './mi_nube' 

# Conexión a AWS
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

class SincronizadorS3(FileSystemEventHandler):
    def on_created(self, event):
        self.subir_archivo(event)

    def on_modified(self, event):
        self.subir_archivo(event)

    def subir_archivo(self, event):
        if event.is_directory:
            return
        
        ruta_local = event.src_path
        nombre_archivo = os.path.basename(ruta_local)
        
        try:
            print(f"Subiendo {nombre_archivo} a AWS...")
            s3_client.upload_file(ruta_local, BUCKET_NAME, nombre_archivo)
            print(f"¡Éxito! '{nombre_archivo}' está en la nube.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if not os.path.exists(CARPETA_A_VIGILAR):
        os.makedirs(CARPETA_A_VIGILAR)

    event_handler = SincronizadorS3()
    observer = Observer()
    observer.schedule(event_handler, CARPETA_A_VIGILAR, recursive=False)
    observer.start()

    print(f"Vigilando carpeta: {os.path.abspath(CARPETA_A_VIGILAR)}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
