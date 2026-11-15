import math

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) using Haversine formula.
    Returns distance in kilometers.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    # Earth radius in kilometers
    R = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    
    # Avoid domain errors due to floating point inaccuracies
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = R * c
    return round(distance, 2)

def calculate_transport_cost(distance_km: float, base_fare: float = 200.0, per_km_rate: float = 25.0) -> float:
    """
    Calculates estimated logistics/transport cost for inter-store transfer.
    For small local transfers (e.g. 8 km), returns base_fare + (distance * per_km_rate).
    Example: 8 km -> 200 + 8 * 25 = 400.
    """
    return round(base_fare + (distance_km * per_km_rate), 2)
