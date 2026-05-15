import os
import time
import boto3
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURACIÓN SEGURA ---
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
BUCKET_NAME = 'sync-archivos-victor'
CARPETA_A_VIGILAR = '/app/mi_nube'  

# --- CLIENTE S3 ---
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name='us-east-2' 
)

# --- LÓGICA DE DETECCIÓN Y SUBIDA ---
class SincronizadorS3(FileSystemEventHandler):
    def procesar_archivo(self, ruta_local):
        nombre_archivo = os.path.basename(ruta_local)
        
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

    # --- NUEVA FUNCIÓN DE LIMPIEZA ---
    def on_deleted(self, event):
        if not event.is_directory:
            nombre_borrado = os.path.basename(event.src_path)
            
            if nombre_borrado.startswith('.'):
                return

            print(f"--- EVENTO: Archivo Eliminado/Renombrado (Viejo) -> {nombre_borrado} ---")
            
            try:
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=nombre_borrado)
                print(f"Limpieza: '{nombre_borrado}' fue eliminado de AWS S3.")
            except Exception as e:
                print(f"Error borrando en S3: {e}")

    # Mantenemos on_moved por si el sistema operativo logra enviarlo
    def on_moved(self, event):
        if not event.is_directory:
            ruta_nueva = event.dest_path
            nombre_viejo = os.path.basename(event.src_path)
            
            print(f"--- EVENTO: Movimiento Directo Detectado ---")
            self.procesar_archivo(ruta_nueva)
            try:
                s3_client.delete_object(Bucket=BUCKET_NAME, Key=nombre_viejo)
            except Exception:
                pass

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