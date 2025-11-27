from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column, Integer, Float, SmallInteger, String, Boolean, LargeBinary, BigInteger, 
    TIMESTAMP, PrimaryKeyConstraint, ForeignKeyConstraint, DateTime, Index 
)
from datetime import datetime

Base = declarative_base()

class Counter(Base):
    __tablename__ = "counters"
    id = Column(SmallInteger, nullable=False)           # counter_id
    device_id = Column(Integer, nullable=False)         # device
    lpp = Column(Float)                                # usa Integer/Real según te convenga
    typ = Column(String(1))
    diagrammdaten = Column(LargeBinary)                 # blob
    created = Column(TIMESTAMP, nullable=True)
    modified = Column(TIMESTAMP, nullable=True)
    aktiv = Column(Boolean, default=True)
    kontrollperiode_ab = Column(String(5))
    kontrollperiode_bis = Column(String(5))
    kumuliertedaten = Column(LargeBinary)
    mindestalarm = Column(BigInteger, default=2000)
    name = Column(String(30))
    customer_id = Column(Integer, default=0)
    last_read = Column(TIMESTAMP, nullable=True)
    send_null = Column(Boolean, default=True)
    send_minimum = Column(Boolean, default=True)
    daily_meters = Column(Integer, default=0)
    flag_sms_sent = Column(Boolean, default=False)
    position = Column(Integer, default=2147483647)
    location = Column(String(250))
    total = Column(Integer, default=0)
    base = Column(Integer, default=0)
    last_seconds = Column(Integer, default=0)

    __table_args__ = (
        PrimaryKeyConstraint('id', 'device_id', name='pk_counters'),
    )

    iec104_config = relationship("Iec104Config", back_populates="counter", uselist=False)

class Iec104Config(Base):
    __tablename__ = "iec104_config"
    device_id = Column(Integer, nullable=False)
    counter_id = Column(Integer, nullable=False)
    remote_ip_1 = Column(String(100), nullable=False)
    remote_ip_2 = Column(String(100), nullable=False)
    local_port = Column(Integer, default=2404)
    common_address = Column(Integer, nullable=False)
    information_object_address = Column(Integer, nullable=False)
    information_object_address_start = Column(Integer, nullable=False)
    send_interval = Column(Integer, default=60)
    enabled = Column(Boolean, default=True)
    flow_unit = Column(String(20), default="l/min")
    agg_periods = Column(String, default="60")

    __table_args__ = (
        PrimaryKeyConstraint('device_id', 'counter_id', name='pk_iec104_config'),
        ForeignKeyConstraint(
            ['device_id', 'counter_id'],
            ['counters.device_id', 'counters.id'],
            ondelete='CASCADE'
        ),
    )

    counter = relationship("Counter", back_populates="iec104_config")

    @property
    def periods(self):
        """
        Devuelve los periodos de agregación como lista de enteros.
        Ejemplo: "3|15|60" -> [3, 15, 60]
        """
        try:
            return [int(p) for p in self.agg_periods.split("|") if p.strip().isdigit()]
        except Exception:
            return []

class Iec104AggregatedData(Base):
    __tablename__ = 'iec104_aggregated_data'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # CLAVE DE IDENTIFICACIÓN (para IEC-104)
    common_address = Column(Integer, nullable=False) # ASDU
    ioa_address = Column(Integer, nullable=False, index=True) # IOA ÚNICA (ej. 100, 101, 102)
    
    # El DATO (lo que se envía)
    timestamp_start = Column(DateTime, nullable=False, index=True) # Hora de inicio del bloque
    value = Column(Float, nullable=False)                          # Valor promedio y convertido
    
    # METADATOS
    period_minutes = Column(Integer) # 3, 15 o 60 (para referencia)
    
    # Gestión de Envío (necesario para la Interrogación General)
    sent_on_gi = Column(Boolean, default=False) # Flag: ¿Ya se envió en una GI?
    created_at = Column(DateTime, default=datetime.now)

    # Creamos un índice compuesto para consultas rápidas
    __table_args__ = (
        Index('idx_asdu_ioa_ts', 'common_address', 'ioa_address', 'timestamp_start'),
    )