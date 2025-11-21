from db import get_session, engine
from models import Base, Counter, Iec104Config

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

def main():


    s = get_session()

    # abrir archivo binario tal cual
    with open("/opt/aqua104/app/counters-1_135_kumuliertedaten.bin", "rb") as f:
        k_blob_bytes = f.read()

    # abrir archivo binario tal cual
    with open("/opt/aqua104/app/counters-1_135_diagrammdaten.bin", "rb") as f:
        d_blob_bytes = f.read()        

    print("Tamaño leído:", len(d_blob_bytes))  # debería dar 1056958
    print("Tamaño leído:", len(k_blob_bytes))  # debería dar 1056958

    # --- COUNTERS DE PRUEBA ---
    # diagrammdaten / kumuliertedaten: leidos de los archivos
    c1 = Counter(
        device_id=135, id=1, name="Counter A", aktiv=True,
        diagrammdaten=d_blob_bytes,
        kumuliertedaten=k_blob_bytes,
        lpp=1.0, typ="A"
    )

    # --- CONFIGS IEC-104 ---
    cfg1 = Iec104Config(
        device_id=135, counter_id=1,
        server_ip="127.0.0.1", server_port=2404,
        common_address=1, information_object_address=1001,
        send_interval=60, enabled=True,
        flow_unit="l/sec", agg_periods="3|15|60"
    )    



    # UPSERT (idempotente)
    s.merge(c1)
    s.merge(cfg1)

    s.commit()

    # Verificación rápida
    print("Seed con BLOB real insertado en SQLite")

    s.close()

if __name__ == "__main__":
    main()
