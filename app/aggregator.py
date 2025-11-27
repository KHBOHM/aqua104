from datetime import datetime, timedelta
from typing import List, Tuple, Dict

def aggregate_by_window(
    raw_series: List[Tuple[datetime, int]],
    window_minutes: int,
    from_dt: datetime,
    to_dt: datetime
) -> List[Tuple[datetime, float]]:
    """
    Promedio la serie minuto a minuto en bloques consecutivos de window_minutes,
    y etiqueto cada promedio con la hora real de inicio del bloque.
    """
    if window_minutes <= 0 or from_dt >= to_dt:
        return []

    # Convierto la serie a un diccionario para acceder por timestamp en O(1).
    series_by_timestamp: Dict[datetime, int] = {
        timestamp: value for timestamp, value in raw_series
    }

    aggregated_series: List[Tuple[datetime, float]] = []
    block_start_time = from_dt

    while block_start_time < to_dt:
        block_values: List[int] = []

        # Recorro los minutos que forman el bloque actual.
        for minute_offset in range(window_minutes):
            current_time = block_start_time + timedelta(minutes=minute_offset)
            if current_time >= to_dt:
                break

            # El blob no debe tener huecos, pero lo dejo robusto igual.
            value = series_by_timestamp.get(current_time)
            if value is not None:
                block_values.append(value)

        if block_values:
            block_average = sum(block_values) / len(block_values)
            aggregated_series.append((block_start_time, block_average))

        # Paso al siguiente bloque.
        block_start_time += timedelta(minutes=window_minutes)

    return aggregated_series

