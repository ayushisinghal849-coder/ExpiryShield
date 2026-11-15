def calculate_percentage(part: float, whole: float) -> float:
    if whole <= 0:
        return 0.0
    return round((part / whole) * 100, 2)

def round_currency(val: float) -> float:
    return round(float(val), 2)
