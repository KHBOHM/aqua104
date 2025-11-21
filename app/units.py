def convert_value(value: float, unit: str) -> float:
    """
    Convierte un valor en l/min a la unidad deseada.
    Soporta: l/min, l/s, m3/min, m3/h.
    """
    if unit == "l/min":
        return value
    elif unit == "l/s":
        return value / 60.0
    elif unit == "m3/min":
        return value / 1000.0
    elif unit == "m3/h":
        return value * 60.0 / 1000.0
    else:
        raise ValueError(f"Unidad de flujo no soportada: {unit}")
