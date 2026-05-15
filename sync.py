import os
import time
import boto3
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURACIÓN SEGURA ---
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = 'sync-archivos-victor'
CARPETA_A_VIGILAR = '/app/mi_nube'  # <-- CAMBIO CLAVE: Ruta absoluta que coincide con el YAML

# --- CLIENTE S3 ---
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='us-east-2'  # <-- CAMBIO CLAVE: Previene bloqueos de conexión
)

# --- LÓGICA DE DETECCIÓN Y SUBIDA ---
class SincronizadorS3(FileSystemEventHandler):
    def procesar_archivo(self, ruta_local):
        nombre_archivo = os.path.basename(ruta_local)
        
        # Escudo: Ignorar archivos temporales u ocultos que crea la red de Windows
        if nombre_archivo.startswith('.'):
            return
            
        try:
            print(f"Procesando archivo: {nombre_archivo}...")
            s3_client.upload_file(ruta_local, BUCKET_NAME, nombre_archivo)
            print(f"¡Éxito! '{nombre_archivo}' subido a la nube correctamente.")
        except Exception as e:
            print(f"ERROR FATAL subiendo a AWS: {e}")

    def on_created(self, event):
        if not event.is_directory:
            print(f"--- EVENTO: Archivo Creado -> {event.src_path} ---")
            self.procesar_archivo(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            print(f"--- EVENTO: Archivo Modificado -> {event.src_path} ---")
            self.procesar_archivo(event.src_path)

# --- INICIO DEL BUCLE ---
if __name__ == "__main__":
    if not os.path.exists(CARPETA_A_VIGILAR):
        os.makedirs(CARPETA_A_VIGILAR)

    event_handler = SincronizadorS3()
    observer = Observer()
    observer.schedule(event_handler, CARPETA_A_VIGILAR, recursive=False)
    observer.start()

    print("==================================================")
    print(f" VIGILANCIA SMB ACTIVA EN: {CARPETA_A_VIGILAR}")
    print("==================================================")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
