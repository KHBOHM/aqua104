from datetime import datetime, timedelta
from db import get_session
from models import Iec104Config
from fetcher import fetch_series
from aggregator import aggregate_series
from units import convert_value
from sender import send_to_scada

def main():
    s = get_session()
    now = datetime.now().replace(second=0, microsecond=0)
    from_dt = now - timedelta(hours=24)
    to_dt = now

    configs = s.query(Iec104Config).filter_by(enabled=True).all()
    for cfg in configs:
        raw_series = fetch_series(cfg.device_id, cfg.counter_id, from_dt, to_dt)

        for period in cfg.periods:
            agg_series = aggregate_series(raw_series, period)
            converted = [(ts, convert_value(val, cfg.flow_unit)) for ts, val in agg_series]
            send_to_scada(cfg, converted)

if __name__ == "__main__":
    main()
