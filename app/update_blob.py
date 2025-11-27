import os
from sqlalchemy import text
from db import get_session
from sqlalchemy.exc import IntegrityError 

# --- CONFIGURACIÓN ---
FILE_NAME = "counters-1_135_kumuliertedaten.bin"
DEVICE_ID = 1
COUNTER_ID = 135

def update_counter_blob():
    # Ruta al archivo: asume que el archivo está en el mismo directorio que el script (app/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, FILE_NAME)
    
    # 1. Leer el archivo binario
    try:
        with open(file_path, 'rb') as f:
            blob_data = f.read()
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo binario en: {file_path}")
        print("Asegúrate de que el archivo se llame '{FILE_NAME}' y esté en la carpeta 'app/'.")
        return
        
    session = get_session()
    
    try:
        # 2. Actualizar el BLOB en la tabla 'counters'
        print(f"Leyendo {len(blob_data)} bytes del archivo...")
        
        # Sentencia UPDATE SQL
        UPDATE_SQL = text("""
            UPDATE counters 
            SET kumuliertedaten = :data 
            WHERE device_id = :device_id AND id = :counter_id;
        """)

        result = session.execute(
            UPDATE_SQL,
            {
                "data": blob_data, 
                "device_id": DEVICE_ID, 
                "counter_id": COUNTER_ID
            }
        )
        
        if result.rowcount == 0:
            print(f"ERROR: No se encontró el contador (Device ID: {DEVICE_ID}, Counter ID: {COUNTER_ID}) para actualizar.")
            print("Asegúrate de haber insertado la configuración (insert_config.py) antes.")
            session.rollback()
        else:
            session.commit()
            print("-------------------------------------------------------")
            print(f"¡Éxito! {len(blob_data)} bytes insertados en 'kumuliertedaten' para el Contador {COUNTER_ID}.")
            print("-------------------------------------------------------")
            
    except Exception as e:
        session.rollback()
        print(f"ERROR grave al actualizar el BLOB: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    update_counter_blob()