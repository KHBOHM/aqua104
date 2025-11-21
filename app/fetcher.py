from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from db import engine
from typing import List, Tuple

# --- helpers de índice ---
def minute_index(dt: datetime) -> int:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    jan1 = datetime(dt.year, 1, 1)
    delta = dt - jan1
    return delta.days * 1440 + delta.seconds // 60

def blob_start_pos(dt: datetime) -> int:
    return minute_index(dt) * 2 + 1

def minutes_between(from_dt: datetime, to_dt: datetime) -> int:
    if from_dt.tzinfo is not None:
        from_dt = from_dt.astimezone(timezone.utc).replace(tzinfo=None)
    if to_dt.tzinfo is not None:
        to_dt = to_dt.astimezone(timezone.utc).replace(tzinfo=None)
    return int((to_dt - from_dt).total_seconds() // 60)

# --- decodificación ---
def _decode_hex_u16_be(hex_str: str) -> List[int]:
    if not hex_str:
        return []
    raw = bytes.fromhex(hex_str)
    if len(raw) % 2 != 0:
        raw = raw[:-1]
    return [int.from_bytes(raw[i:i+2], "big") for i in range(0, len(raw), 2)]

# --- función principal ---
def fetch_series(
    device_id: int,
    counter_id: int,
    from_dt: datetime,
    to_dt: datetime,
    field: str = "kumuliertedaten"   # usamos crudo por defecto
) -> List[Tuple[datetime, int]]:
    assert to_dt > from_dt, "to_dt debe ser posterior a from_dt"
    minutes = minutes_between(from_dt, to_dt)
    if minutes <= 0:
        return []

    start = blob_start_pos(from_dt)
    length = minutes * 2
    dialect = engine.dialect.name

    if dialect == "sqlite":
        sql = f"""
            SELECT HEX(SUBSTR({field}, :start, :length)) AS hexdata
            FROM counters
            WHERE device_id = :device_id AND id = :counter_id
        """
    elif dialect in ("postgresql", "postgres"):
        sql = f"""
            SELECT ENCODE(SUBSTRING({field} FROM :start FOR :length), 'hex') AS hexdata
            FROM counters
            WHERE device_id = :device_id AND id = :counter_id
        """
    else:
        raise NotImplementedError(f"DB dialect '{dialect}' no soportado")

    with engine.connect() as conn:
        row = conn.execute(
            text(sql),
            dict(start=start, length=length, device_id=device_id, counter_id=counter_id)
        ).mappings().first()

    hexdata = row["hexdata"] if row and row["hexdata"] else ""
    values = _decode_hex_u16_be(hexdata)

    series = []
    t = from_dt
    for v in values:
        series.append((t, v))
        t += timedelta(minutes=1)
    return series
