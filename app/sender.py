from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List

# --- Importación de la librería c104 ---
from c104.enums import CauseOfTransmission as COT, TypeId as TI
from c104.slave import Slave
from c104.io import I, ASDU, GI
from c104.timestamp import Timestamp
from c104.datagram import Datagram

from db import get_session
from models import Iec104Config, Iec104AggregatedData

# --- CLASE HANDLER: GESTIONA LA LÓGICA DE DATOS ---

class Aqua104DataHandler:
    """
    Gestiona los callbacks del protocolo IEC 104 que interactúan con la DB.
    """
    def __init__(self, config: Iec104Config, slave_server):
        self.config = config
        self.slave_server = slave_server # Referencia al objeto Slave para enviar

    # El callback principal que maneja la Interrogación General (GI)
    def on_gi(self, asdu: ASDU, gi: GI) -> None:
        """
        CALLBACK: Se ejecuta cuando el Master (PSIprins) envía C_IC_NA_1.
        """
        session: Optional[Session] = None
        sent_count = 0
        
        try:
            conn_id = 1 # c104 normalmente maneja la conexión internamente

            print(f"\n Master solicitó Interrogación General (GI) para ASDU {asdu.value}.")
            session = get_session()
            
            # 1. QUERY DE LA DB: Traer todos los datos agregados y no enviados.
            data_to_send: List[Iec104AggregatedData] = (
                session.query(Iec104AggregatedData)
                .filter(
                    Iec104AggregatedData.common_address == self.config.common_address,
                    Iec104AggregatedData.sent_on_gi == False
                )
                .order_by(
                    Iec104AggregatedData.ioa_address,
                    Iec104AggregatedData.timestamp_start
                )
                .all()
            )
            
            # 2. Enviar respuesta de 'Activación' de la GI (Act/Con)
            # Esto debe hacerse antes de enviar los datos
            self.slave_server.send_gi_response(
                asdu=asdu, 
                ti=TI.C_IC_NA_1,
                cot=COT.ACTIVATION_CON
            )

            # 3. Enviar cada dato como M_ME_TD_1 (Valor Normalizado con Time Tag)
            for data in data_to_send:
                # Calidad (Quality Flags): Asumimos válido (0)
                quality_flags = 0 
                
                # Usamos el timestamp_start del bloque de datos
                timestamp = Timestamp.from_datetime(data.timestamp_start)
                
                # Crear el objeto de información (I) para enviar
                # Usamos TI.M_ME_TD_1 (Type Identification 13: Valor normalizado con tiempo)
                info_object = I(
                    ioa=data.ioa_address,
                    normalized_value=data.value, 
                    quality=quality_flags,
                    timestamp=timestamp
                )

                # Envío de la Trama
                self.slave_server.send_asdu(
                    asdu=asdu,
                    ti=TI.M_ME_TD_1, 
                    io=info_object,
                    cot=COT.SPONTANEOUS # La GI se responde con COT Spontaneous
                )
                
                # 4. Marcar como enviado y actualizar la DB
                data.sent_on_gi = True
                session.add(data)
                sent_count += 1
                
            session.commit()
            
            # 5. Enviar respuesta de 'Terminación' de la GI (Act/Term)
            self.slave_server.send_gi_response(
                asdu=asdu, 
                ti=TI.C_IC_NA_1, 
                cot=COT.ACTIVATION_TERM
            )

            print(f"GI finalizada. Enviados {sent_count} objetos de información.")
            
        except Exception as e:
            print(f"Error en el manejo de GI: {e}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

# --- FUNCIÓN PRINCIPAL DEL SERVIDOR ---

def run_iec104_slave():
    """Inicializa y corre el servidor IEC 104 Slave."""
    session = get_session()
    
    # 1. Obtener la primera configuración activa (ASDU)
    config: Iec104Config = (
        session.query(Iec104Config)
        .filter(Iec104Config.enabled == True)
        .first()
    )
    session.close()

    if not config:
        print("ERROR: No se encontró configuración IEC 104 habilitada en la DB.")
        return

    # 2. Inicializar el Servidor Slave con las IPs y puerto.
    # El puerto y la IP se configuran directamente.
    slave_server = Slave(
        host='0.0.0.0', 
        port=config.local_port,
        asdu_address=config.common_address, # Se establece el ASDU principal
        asdu_size=2,  # ¡ATENCIÓN! Usar el valor que indique la ASG
        ioa_size=3    # ¡ATENCIÓN! Usar el valor que indique la ASG
    )

    # 3. Configurar las IPs Master permitidas (redundancia)
    slave_server.add_master(config.remote_ip_1)
    slave_server.add_master(config.remote_ip_2)
    
    # 4. Asignar el Handler personalizado al servidor
    handler = Aqua104DataHandler(config, slave_server)
    slave_server.set_gi_handler(handler.on_gi) # El handler de la Interrogación General

    # 5. Iniciar el Servidor
    try:
        print(f"Iniciando IEC 104 Slave en puerto TCP/{config.local_port}...")
        print(f"Masters autorizados: {config.remote_ip_1}, {config.remote_ip_2}")
        slave_server.run()
    except KeyboardInterrupt:
        print("Servidor detenido por el usuario.")
    except Exception as e:
        print(f"Fallo grave del servidor: {e}")
    finally:
        slave_server.stop()

if __name__ == "__main__":
    run_iec104_slave()