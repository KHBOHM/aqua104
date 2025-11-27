from sqlalchemy import text
from db import get_session
from sqlalchemy.exc import IntegrityError 

# --- CONFIGURACIÓN DE PRUEBA ---
DEVICE_ID = 1
COUNTER_ID = 135

# 1. SQL para insertar el Counter (Contador)
# Incluye campos NOT NULL: id, device_id, typ, mindestalarm, name, customer_id, daily_meters, flag_sms_sent, position, total, base, last_seconds
# Excluye campos LargeBinary (BLOBs) que no son NOT NULL.
INSERT_COUNTER_SQL = f"""
INSERT OR IGNORE INTO counters (
    id, device_id, typ, name, customer_id, daily_meters, 
    flag_sms_sent, position, total, base, last_seconds
) VALUES (
    {COUNTER_ID}, 
    {DEVICE_ID}, 
    'F',                                      -- typ (String(1), NOT NULL. Usamos 'F' de Flow)
    'Contador de Prueba {COUNTER_ID}',       -- name (String(30), NOT NULL)
    0,                                        -- customer_id
    0,                                        -- daily_meters
    0,                                        -- flag_sms_sent (Boolean, 0 para False)
    2147483647,                               -- position (Integer, default=2147483647)
    0,                                        -- total
    0,                                        -- base
    0                                         -- last_seconds
);
"""

# 2. SQL para insertar la Configuración IEC 104
# Incluye todos los 12 campos NOT NULL de Iec104Config.
INSERT_IEC104_CONFIG_SQL = f"""
INSERT INTO iec104_config (
    device_id, counter_id, remote_ip_1, remote_ip_2, local_port, common_address, 
    information_object_address, information_object_address_start, send_interval, 
    enabled, flow_unit, agg_periods
) VALUES (
    {DEVICE_ID}, 
    {COUNTER_ID}, 
    '192.168.10.10',                          -- remote_ip_1
    '192.168.10.11',                          -- remote_ip_2
    2404,                                     -- local_port
    100,                                      -- common_address (ASDU)
    5000,                                     -- information_object_address (IOA Base)
    5000,                                     -- information_object_address_start
    60,                                       -- send_interval (en segundos)
    1,                                        -- enabled (1 para True)
    'm3/h',                                   -- flow_unit
    '3|15|60'                                 -- agg_periods
);
"""

def insert_config():
    session = get_session()
    try:
        print(f"1. Asegurando que el contador ({DEVICE_ID}, {COUNTER_ID}) exista...")
        # Ejecuta la inserción del contador. INSERT OR IGNORE previene errores si ya existe.
        session.execute(text(INSERT_COUNTER_SQL))
        
        print("2. Insertando configuración IEC 104...")
        # Ejecuta la inserción de la configuración.
        session.execute(text(INSERT_IEC104_CONFIG_SQL))
        
        session.commit()
        print("-------------------------------------------------------")
        print("Configuración IEC 104 y Contador de prueba insertados con éxito.")
        print("-------------------------------------------------------")
        
    except IntegrityError as e:
        session.rollback()
        # Captura errores de unicidad (ej. intentar insertar la misma configuración dos veces)
        if "UNIQUE constraint failed" in str(e):
            print("ERROR: La configuración ya existe. No se hicieron cambios.")
        else:
            print(f"Error de integridad al insertar: {e}")
            
    except Exception as e:
        session.rollback()
        print(f"Error desconocido al insertar configuración: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    insert_config()