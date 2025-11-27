from datetime import datetime, timedelta, timezone
from db import get_session
from sqlalchemy import text
from struct import pack
from typing import Optional

# --- Valores de configuración para el contador (DEBEN COINCIDIR) ---
DEVICE_ID = 1
COUNTER_ID = 135
BLOB_FIELD = "kumuliertedaten" # El campo que lee main.py

# --- Funciones auxiliares (replicadas de fetcher.py/blob_read.py) ---

def minute_index(dt: datetime) -> int:
    """Calcula el índice de minuto del año (0-based)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    jan1 = datetime(dt.year, 1, 1)
    delta = dt - jan1
    return delta.days * 1440 + delta.seconds // 60

def generate_test_data(minutes_to_generate: int = 1440) -> bytes:
    """Genera datos de 2 bytes (uint16 Big Endian) simulando flujo constante."""
    # Simula 500 litros/min (valor seguro para uint16)
    FLOW_VALUE = 500 
    data = b''
    for _ in range(minutes_to_generate):
        # '>H' = Big Endian Unsigned Short (2 bytes)
        data += pack('>H', FLOW_VALUE)
    return data

def insert_test_blob():
    session = get_session()
    
    # 1. Definir el rango de tiempo a simular (las últimas 24 horas)
    now = datetime.now().replace(second=0, microsecond=0)
    from_dt = now - timedelta(hours=24)
    minutes_in_year = 366 * 1440 if now.year % 4 == 0 else 365 * 1440
    
    # 2. Calcular la posición de inicio en el BLOB (en bytes)
    start_minute_index = minute_index(from_dt)
    start_byte_pos = start_minute_index * 2
    
    # 3. Generar 24 horas (1440 minutos) de datos de prueba
    test_data = generate_test_data(minutes_to_generate=1440)
    data_length = len(test_data)
    full_year_bytes = minutes_in_year * 2
    
    try:
        # Paso A: Leer el BLOB actual
        current_blob: Optional[bytes] = session.execute(
            text(f"SELECT {BLOB_FIELD} FROM counters WHERE id = :counter_id AND device_id = :device_id"),
            {"counter_id": COUNTER_ID, "device_id": DEVICE_ID}
        ).scalar()

        # Paso B: Pre-llenar el BLOB si es demasiado pequeño (simular un año)
        # Esto es vital para que la función SUBSTR de SQLite funcione.
        if not current_blob or len(current_blob) < full_year_bytes:
             print(f"Pre-llenando {BLOB_FIELD} con {full_year_bytes} bytes (simulación de un año) con ceros...")
             current_blob = b'\x00' * full_year_bytes
             
        # Paso C: Inyectar los datos de prueba en la posición correcta
        new_blob = (
            current_blob[:start_byte_pos] + 
            test_data + 
            current_blob[start_byte_pos + data_length:]
        )
        
        # Paso D: Actualizar la base de datos
        session.execute(
            text(f"UPDATE counters SET {BLOB_FIELD} = :new_data WHERE id = :counter_id AND device_id = :device_id"),
            {"new_data": new_blob, "counter_id": COUNTER_ID, "device_id": DEVICE_ID}
        )
        
        session.commit()
        print("-------------------------------------------------------")
        print(f"BLOB '{BLOB_FIELD}' actualizado exitosamente.")
        print(f"Datos insertados: {data_length} bytes (1440 minutos) simulando 500 l/min.")
        print(f"El rango de tiempo simulado es de 24 horas hasta {now}.")
        print("-------------------------------------------------------")
        
    except Exception as e:
        session.rollback()
        print(f"ERROR: Falló la inserción del BLOB: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    insert_test_blob()