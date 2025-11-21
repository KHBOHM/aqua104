from datetime import datetime, timedelta
from typing import List, Tuple

def aggregate_series(
    series: List[Tuple[datetime, int]],
    window_minutes: int
) -> List[Tuple[datetime, float]]:
    if not series or window_minutes <= 0:
        return []

    aggregated = []
    block = []
    block_start = series[0][0]

    for ts, val in series:
        block.append(val)
        elapsed = int((ts - block_start).total_seconds() // 60) + 1
        if elapsed >= window_minutes:
            avg = sum(block) / len(block)
            aggregated.append((block_start, avg))
            block = []
            block_start = ts + timedelta(minutes=1)

    if block:
        avg = sum(block) / len(block)
        aggregated.append((block_start, avg))

    return aggregated
