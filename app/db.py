from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# DSN local (SQLite). Para producción (PostgreSQL) cambia esta línea.
DB_DSN = "sqlite:////opt/aqua104/app/local.sqlite"
# Ejemplo Postgres: "postgresql+psycopg2://user:pass@localhost/dbname"

engine = create_engine(DB_DSN, echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_session():
    """Devuelve una sesión SQLAlchemy lista para usar."""
    return SessionLocal()
