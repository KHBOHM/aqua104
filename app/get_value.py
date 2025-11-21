from datetime import datetime
from fetcher import fetch_series
from db import get_session
from models import Counter

def main():
    print("=== Consulta de valor minuto a minuto ===")
    device_id = int(input("Device ID: "))
    counter_id = int(input("Counter ID: "))
    date_str = input("Fecha y hora (dd.mm.YYYY HH:MM): ")

    try:
        dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
    except ValueError:
        print("Formato inválido. Usa dd.mm.YYYY HH:MM")
        return

    # obtenemos un rango de 1 minuto
    series = fetch_series(device_id, counter_id, dt, dt.replace(second=0) + timedelta(minutes=1))

    if not series:
        print("No se encontró dato para esa fecha")
        return

    ts, value = series[0]
    print(f"Valor en {ts} -> {value}")

if __name__ == "__main__":
    from datetime import timedelta
    main()
