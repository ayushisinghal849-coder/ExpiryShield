import re
from datetime import datetime, date
from typing import Tuple, Optional

def validate_positive_number(value: float, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be a positive number.")

def parse_iso_date(date_str: str) -> date:
    """Parses date string in YYYY-MM-DD or DD/MM/YYYY format."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Invalid date format for '{date_str}'. Expected YYYY-MM-DD.")
