# /opt/aqua104/app/blob_read.py
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from db import engine
from typing import List, Tuple, Literal

# --- helpers de índice (equivalentes a tus _indexMinute y _indexBlob) ---

def minute_index(dt: datetime) -> int:
    """
    Minuto del año (0..525599). Acepta naive (se asume local) o aware.
    """
    # normalizamos a naive para cálculo simple (ajusta si querés TZ)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    jan1 = datetime(dt.year, 1, 1)
    delta = dt - jan1
    return delta.days * 1440 + delta.seconds // 60

def blob_start_pos(dt: datetime) -> int:
    """
    Posición 1-based dentro del BLOB (2 bytes por minuto) => minute*2 + 1
    """
    return minute_index(dt) * 2 + 1

def minutes_between(from_dt: datetime, to_dt: datetime) -> int:
    """
    Cantidad de minutos entre from (incluido) y to (exclusivo).
    """
    if from_dt.tzinfo is not None:
        from_dt = from_dt.astimezone(timezone.utc).replace(tzinfo=None)
    if to_dt.tzinfo is not None:
        to_dt = to_dt.astimezone(timezone.utc).replace(tzinfo=None)
    return int((to_dt - from_dt).total_seconds() // 60)

# --- extracción SQL dependiente de motor ---

def _select_hex_sql(dialect: str, field: Literal["diagrammdaten","kumuliertedaten"]) -> str:
    """
    Devuelve el SELECT que retorna un único valor 'hexdata' con el segmento hex.
    - SQLite: HEX(SUBSTR(blob, start, len))
    - Postgres: ENCODE(SUBSTRING(blob FROM start FOR len), 'hex')
    """
    if dialect == "sqlite":
        return f"""
            SELECT HEX(SUBSTR({field}, :start, :length)) AS hexdata
            FROM counters
            WHERE device_id = :device_id AND id = :counter_id
        """
    elif dialect in ("postgresql", "postgres"):
        return f"""
            SELECT ENCODE(SUBSTRING({field} FROM :start FOR :length), 'hex') AS hexdata
            FROM counters
            WHERE device_id = :device_id AND id = :counter_id
        """
    else:
        # Podés agregar MySQL si querés (HEX(SUBSTRING(...)))
        raise NotImplementedError(f"DB dialect '{dialect}' no soportado aún")

# --- decodificación del hex a lista de uint16 ---

def _decode_hex_u16_be(hex_str: str) -> List[int]:
    """
    Decodifica una cadena hex (longitud par) en una lista de enteros uint16 big-endian.
    """
    if not hex_str:
        return []
    raw = bytes.fromhex(hex_str)
    if len(raw) % 2 != 0:
        # Si llega impar, recortamos el último byte por seguridad (no debería pasar)
        raw = raw[:-1]
    out = []
    for i in range(0, len(raw), 2):
        out.append(int.from_bytes(raw[i:i+2], byteorder="big", signed=False))
    return out

# --- API pública: extraer una serie minuto a minuto ---

def fetch_series(
    device_id: int,
    counter_id: int,
    from_dt: datetime,
    to_dt: datetime,
    field: Literal["diagrammdaten","kumuliertedaten"] = "diagrammdaten",
) -> List[Tuple[datetime, int]]:
    """
    Extrae (timestamp_minuto, valor_uint16) para [from_dt, to_dt) desde 'field'.
    Devuelve lista ordenada por tiempo.
    """
    assert to_dt > from_dt, "to_dt debe ser posterior a from_dt"
    minutes = minutes_between(from_dt, to_dt)
    if minutes <= 0:
        return []

    start = blob_start_pos(from_dt)
    length = minutes * 2  # 2 bytes por minuto

    dialect = engine.dialect.name
    sql = _select_hex_sql(dialect, field)

    with engine.connect() as conn:
        row = conn.execute(
            text(sql),
            dict(start=start, length=length, device_id=device_id, counter_id=counter_id)
        ).mappings().first()

    hexdata = row["hexdata"] if row and row["hexdata"] is not None else ""
    values = _decode_hex_u16_be(hexdata)

    # construir timestamps por minuto
    out = []
    t = from_dt
    for v in values:
        out.append((t, v))
        t += timedelta(minutes=1)

    return out

# --- ejemplo de uso manual (quitar/ajustar a gusto) ---
if __name__ == "__main__":
    # ejemplo: leer 60 min desde hoy 00:00
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    serie = fetch_series(device_id=100, counter_id=1, from_dt=today, to_dt=today + timedelta(hours=1))
    print(f"Leídos {len(serie)} puntos")
    if serie:
        print(serie[:5], "...")
