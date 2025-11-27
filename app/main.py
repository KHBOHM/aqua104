from datetime import datetime, timedelta

from db import get_session
from models import Iec104Config, Iec104AggregatedData 
from fetcher import fetch_series
from aggregator import aggregate_by_window
from units import convert_value
# from sender import send_to_scada # Ya no se usa aquí


def run_daily_export() -> None:
    """
    Este es el orquestador principal.
    Lee configs, extrae datos, calcula promedios/convierte y ALMACENA el resultado
    en la tabla Iec104AggregatedData, listo para ser enviado por el servidor IEC-104.
    """

    database_session = get_session()

    # Rango de trabajo: últimas 24 horas hasta el minuto actual.
    execution_time = datetime.now().replace(second=0, microsecond=0)
    to_datetime = execution_time
    from_datetime = to_datetime - timedelta(hours=24)

    enabled_configs = (
        database_session.query(Iec104Config)
        .filter_by(enabled=True)
        .all()
    )
    
    saved_count = 0

    for config in enabled_configs:
        device_id = config.device_id
        counter_id = config.counter_id
        asdu = config.common_address
        base_ioa = config.information_object_address # IOA base del medidor

        # 1. Leer la serie cruda minuto a minuto (l/min) desde kumuliertedaten.
        raw_minute_series = fetch_series(
            device_id=device_id,
            counter_id=counter_id,
            from_dt=from_datetime,
            to_dt=to_datetime,
            field="kumuliertedaten"
        )

        # 2. Procesar y almacenar para cada ventana pedida.
        # USAMOS ENUMERATE PARA OBTENER EL ÍNDICE (ioa_offset)
        for ioa_offset, window_minutes in enumerate(config.periods):
            
            # Cálculo de los promedios por reloj.
            averaged_series = aggregate_by_window(
                raw_series=raw_minute_series,
                window_minutes=window_minutes,
                from_dt=from_datetime,
                to_dt=to_datetime
            )

            # Cálculo de la IOA única (IOA base + índice del periodo)
            unique_ioa = base_ioa + ioa_offset

            # 3. Guardar cada dato procesado en el buffer de la DB.
            for timestamp, raw_average_value in averaged_series:
                
                # Convertir el valor a la unidad solicitada por el cliente.
                converted_value = convert_value(raw_average_value, config.flow_unit)
                
                # Crear el objeto de dato agregado.
                new_data = Iec104AggregatedData(
                    common_address=asdu,
                    ioa_address=unique_ioa, # IOA única
                    period_minutes=window_minutes,
                    timestamp_start=timestamp,
                    value=converted_value
                )
                
                database_session.add(new_data)
                saved_count += 1

    # 4. Confirmar todos los cambios.
    database_session.commit()
    database_session.close()
    
    print(f"Proceso de agregación finalizado. Se guardaron {saved_count} datos en el buffer.")


if __name__ == "__main__":
    run_daily_export()