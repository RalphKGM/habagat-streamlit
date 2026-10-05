"""Hourly demand scenario and battery dispatch.

Copied verbatim from the research project's ``src/run_demand_storage_simulation.py``.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

BATTERY_POWER_MW = 1.0
CHARGE_EFFICIENCY = 0.95
DISCHARGE_EFFICIENCY = 0.95
MIN_SOC_FRACTION = 0.10
MAX_SOC_FRACTION = 0.90
INITIAL_SOC_FRACTION = 0.10


def synthetic_load_mw(hour: pd.Series) -> np.ndarray:
    """Return the agreed base daily profile in MW."""
    h = hour.to_numpy(dtype=int)
    return np.select(
        [h <= 5, h <= 8, h <= 16, h <= 21],
        [0.25, 0.40, 0.50, 0.65],
        default=0.35,
    ).astype(float)


def simulate_battery(
    generation_mw: np.ndarray,
    demand_mw: np.ndarray,
    capacity_mwh: float,
    initial_soc_mwh: Optional[float] = None,
) -> pd.DataFrame:
    """Follow one site and scenario in time order using a one-hour step."""
    n = len(generation_mw)
    renewable_to_load = np.minimum(generation_mw, demand_mw)
    battery_charge_input = np.zeros(n)
    battery_discharge_to_load = np.zeros(n)
    grid_import = np.zeros(n)
    curtailed = np.zeros(n)
    soc_start = np.zeros(n)
    soc_end = np.zeros(n)

    if capacity_mwh <= 0.0:
        grid_import = np.maximum(demand_mw - renewable_to_load, 0.0)
        curtailed = np.maximum(generation_mw - renewable_to_load, 0.0)
        return pd.DataFrame(
            {
                "renewable_to_load_mwh": renewable_to_load,
                "battery_charge_input_mwh": battery_charge_input,
                "battery_discharge_to_load_mwh": battery_discharge_to_load,
                "grid_import_mwh": grid_import,
                "curtailed_renewable_mwh": curtailed,
                "battery_soc_start_mwh": soc_start,
                "battery_soc_end_mwh": soc_end,
            }
        )

    min_soc = capacity_mwh * MIN_SOC_FRACTION
    max_soc = capacity_mwh * MAX_SOC_FRACTION
    soc = (
        capacity_mwh * INITIAL_SOC_FRACTION
        if initial_soc_mwh is None
        else float(initial_soc_mwh)
    )
    if not min_soc <= soc <= max_soc:
        raise ValueError(
            f"initial_soc_mwh must be between {min_soc:.3f} and {max_soc:.3f} MWh"
        )

    for i, (generation, demand) in enumerate(zip(generation_mw, demand_mw)):
        soc_start[i] = soc
        surplus = max(generation - demand, 0.0)
        deficit = max(demand - generation, 0.0)

        charge_input = min(
            surplus,
            BATTERY_POWER_MW,
            max((max_soc - soc) / CHARGE_EFFICIENCY, 0.0),
        )
        soc += charge_input * CHARGE_EFFICIENCY

        discharge_to_load = min(
            deficit,
            BATTERY_POWER_MW,
            max((soc - min_soc) * DISCHARGE_EFFICIENCY, 0.0),
        )
        soc -= discharge_to_load / DISCHARGE_EFFICIENCY
        soc = min(max(soc, min_soc), max_soc)

        battery_charge_input[i] = charge_input
        battery_discharge_to_load[i] = discharge_to_load
        grid_import[i] = max(deficit - discharge_to_load, 0.0)
        curtailed[i] = max(surplus - charge_input, 0.0)
        soc_end[i] = soc

    return pd.DataFrame(
        {
            "renewable_to_load_mwh": renewable_to_load,
            "battery_charge_input_mwh": battery_charge_input,
            "battery_discharge_to_load_mwh": battery_discharge_to_load,
            "grid_import_mwh": grid_import,
            "curtailed_renewable_mwh": curtailed,
            "battery_soc_start_mwh": soc_start,
            "battery_soc_end_mwh": soc_end,
        }
    )


