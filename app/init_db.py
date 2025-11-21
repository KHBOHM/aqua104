# /opt/aqua104/app/init_db.py
from db import engine
from models import Base

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("SQLite schema created at /opt/aqua104/app/local.sqlite")
