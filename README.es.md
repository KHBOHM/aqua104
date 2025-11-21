# Aqua104 – Envío de Datos IEC 60870-5-104

Este proyecto forma parte del sistema AQUA-DATA GmbH y tiene como objetivo
procesar datos minuto a minuto provenientes de dispositivos IoT de monitoreo
hidráulico, para luego enviarlos de manera agregada a servidores SCADA mediante
el protocolo **IEC 60870-5-104**.

Este repositorio se incluye en mi portfolio técnico como ejemplo de desarrollo
aplicado a sistemas industriales reales.

## ✔ Descripción general

El módulo Aqua104 permite:

- Leer datos crudos minuto a minuto desde la base de datos (`kumuliertedaten`).
- Decodificar valores almacenados en formato binario (BLOB).
- Calcular promedios de flujo en ventanas configurables (por ejemplo: 3, 15, 60 minutos).
- Convertir automáticamente las unidades de flujo (l/min, l/s, m³/min, m³/h).
- Preparar la arquitectura para transmitir datos mediante IEC 60870-5-104.
- Ofrecer una herramienta de consola para consultar el valor de un medidor en una fecha específica.

## ✔ Arquitectura del proyecto

```
aqua104/
 ├─ app/
 │   ├─ models.py          # Modelos SQLAlchemy
 │   ├─ db.py              # Conexión y sesión
 │   ├─ fetcher.py         # Lectura y decodificación de BLOBs
 │   ├─ aggregator.py      # Cálculo de promedios
 │   ├─ units.py           # Conversión de unidades
 │   ├─ sender.py          # (Pendiente) Implementación IEC-104
 │   ├─ main.py            # Proceso completo
 │   ├─ get_value.py       # Herramienta de consulta puntual
 │   ├─ init_db.py         # Creación del esquema
 │   └─ seed_db.py         # Datos iniciales de prueba
 ├─ requirements.txt
 └─ README.es.md
```

## ✔ Instalación

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
```

## ✔ Inicializar base de datos local

```bash
python init_db.py
python seed_db.py
```

## ✔ Uso de herramientas

### Consultar el valor puntual de un medidor:

```bash
python get_value.py
```

### Ejecutar el procesamiento completo:

```bash
python main.py
```

## ✔ Estado actual del proyecto


- **Completado**
  - Arquitectura base en Python
  - Lectura y decodificación de BLOBs
  - Cálculo de promedios configurables
  - Conversión de unidades
  - Herramienta CLI de consulta puntual
  - 

- **Pendiente**
  - Construcción y envío de tramas IEC 60870-5-104
  - Pruebas automáticas
  - Documentación técnica ampliada
  - Versiones del README en inglés y alemán


## ✔ Autor

**Claudio Juan Böhm**  
Backend Developer – PHP / Python – Sistemas IoT  
Proyecto desarrollado para **AQUA-DATA GmbH**, Alemania.


