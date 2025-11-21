from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (create_engine, Column, Integer, Float, SmallInteger, String, Boolean, LargeBinary, BigInteger, TIMESTAMP, PrimaryKeyConstraint, ForeignKeyConstraint)

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
    server_ip = Column(String(100), nullable=False)
    server_port = Column(Integer, default=2404)
    common_address = Column(Integer, nullable=False)
    information_object_address = Column(Integer, nullable=False)
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