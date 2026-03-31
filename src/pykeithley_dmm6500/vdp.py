"""Van der Pauw sheet resistance calculation utilities."""

import math
from typing import NamedTuple
from typing import Optional


class VdpResult(NamedTuple):
    """Result of a Van der Pauw calculation.

    Attributes:
        r_horizontal: Horizontal resistance (V/I) in ohms.
        r_vertical: Vertical resistance (V/I) in ohms.
        sheet_resistance: Sheet resistance R_s in ohms/square.
        resistivity: Resistivity in ohm-cm (if thickness provided, else None).
    """

    r_horizontal: float
    r_vertical: float
    sheet_resistance: float
    resistivity: Optional[float]


def sheet_resistance(
    v_horizontal: float,
    v_vertical: float,
    current: float,
    thickness_cm: Optional[float] = None,
) -> VdpResult:
    """Calculate sheet resistance from Van der Pauw measurements.

    Uses the averaged horizontal and vertical resistance pairs:
        R_s = (pi / ln(2)) * (R_h + R_v) / 2

    This is the symmetric approximation valid when R_h and R_v are similar.
    For samples where R_h and R_v differ significantly, use
    sheet_resistance_iterative() for exact results.

    Args:
        v_horizontal: Averaged voltage from horizontal configs (V).
            Typically average of |V_cfg1| and |V_cfg2| (forward/reverse).
        v_vertical: Averaged voltage from vertical configs (V).
            Typically average of |V_cfg3| and |V_cfg4| (forward/reverse).
        current: Source current in amps.
        thickness_cm: Film thickness in cm (optional, for resistivity).

    Returns:
        VdpResult with sheet resistance and optional resistivity.
    """
    r_h = abs(v_horizontal) / current
    r_v = abs(v_vertical) / current

    rs = (math.pi / math.log(2)) * (r_h + r_v) / 2

    resistivity = None
    if thickness_cm is not None:
        resistivity = rs * thickness_cm

    return VdpResult(
        r_horizontal=r_h,
        r_vertical=r_v,
        sheet_resistance=rs,
        resistivity=resistivity,
    )


def sheet_resistance_from_configs(
    v1: float,
    v2: float,
    v3: float,
    v4: float,
    current: float,
    thickness_cm: Optional[float] = None,
) -> VdpResult:
    """Calculate sheet resistance from all 4 Van der Pauw configurations.

    Averages forward/reverse pairs to cancel offsets:
        V_horizontal = (|V1| + |V2|) / 2
        V_vertical   = (|V3| + |V4|) / 2

    Args:
        v1: Voltage from configuration 1 (V).
        v2: Voltage from configuration 2 (reverse of cfg 1) (V).
        v3: Voltage from configuration 3 (V).
        v4: Voltage from configuration 4 (reverse of cfg 3) (V).
        current: Source current in amps.
        thickness_cm: Film thickness in cm (optional, for resistivity).

    Returns:
        VdpResult with sheet resistance and optional resistivity.
    """
    v_horizontal = (abs(v1) + abs(v2)) / 2
    v_vertical = (abs(v3) + abs(v4)) / 2

    return sheet_resistance(
        v_horizontal=v_horizontal,
        v_vertical=v_vertical,
        current=current,
        thickness_cm=thickness_cm,
    )
