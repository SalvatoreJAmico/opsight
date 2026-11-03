"""Shared validation for simple, chronological record-step forecasts."""
import math

import pandas as pd


def prepare_time_series(records, *, minimum=1):
    usable = [record for record in records
              if record.value is not None and math.isfinite(record.value)]
    if len(usable) < minimum:
        raise ValueError(f"Forecasting requires at least {minimum} finite numeric observation{'s' if minimum != 1 else ''}.")
    timestamps = pd.to_datetime(
        [record.timestamp for record in usable], errors="coerce", format="mixed", utc=True
    )
    if timestamps.isna().any():
        raise ValueError("Forecasting requires a valid timestamp for every usable numeric observation.")
    # Python's stable sort retains source order among equal timestamps.
    return [record for _, record in sorted(zip(timestamps, usable), key=lambda item: item[0])]


def validate_horizon(steps_ahead):
    if isinstance(steps_ahead, bool) or not isinstance(steps_ahead, int) or not 0 <= steps_ahead <= 365:
        raise ValueError("steps_ahead must be an integer from 0 to 365.")
