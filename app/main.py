from datetime import datetime, timedelta

from db import get_session
from models import Iec104Config
from fetcher import fetch_series
from aggregator import aggregate_by_window
from units import convert_value
from sender import send_to_scada


def run_daily_export() -> None:
    """
    Este es el orquestador principal.
    Lo ejecuta un cron una vez al día (aprox. 06:00).
    Leo las configuraciones activas, extraigo los datos crudos de las últimas 24h,
    calculo los promedios por ventanas configuradas, convierto unidades y envío.
    """

    # Obtengo una sesión a la base.
    database_session = get_session()

    # Defino el rango de trabajo: últimas 24 horas hasta el minuto actual.
    execution_time = datetime.now().replace(second=0, microsecond=0)
    to_datetime = execution_time
    from_datetime = to_datetime - timedelta(hours=24)

    # Traigo todas las configuraciones habilitadas.
    enabled_configs = (
        database_session.query(Iec104Config)
        .filter_by(enabled=True)
        .all()
    )

    for config in enabled_configs:
        device_id = config.device_id
        counter_id = config.counter_id

        # Leo la serie cruda minuto a minuto (l/min) desde kumuliertedaten.
        raw_minute_series = fetch_series(
            device_id=device_id,
            counter_id=counter_id,
            from_dt=from_datetime,
            to_dt=to_datetime,
            field="kumuliertedaten"
        )

        # Para cada ventana pedida (ej. 3|15|60) calculo los promedios por reloj.
        for window_minutes in config.periods:
            averaged_series = aggregate_by_window(
                raw_series=raw_minute_series,
                window_minutes=window_minutes,
                from_dt=from_datetime,
                to_dt=to_datetime
            )

            # Convierto cada promedio a la unidad solicitada por el cliente.
            converted_series = [
                (timestamp, convert_value(value, config.flow_unit))
                for timestamp, value in averaged_series
            ]

            # Envío la serie ya procesada.
            # send_to_scada es placeholder por ahora; luego irá IEC-104 real.
            send_to_scada(config, converted_series)


if __name__ == "__main__":
    run_daily_export()
