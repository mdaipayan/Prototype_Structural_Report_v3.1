"""Reusable design calculations extracted from the uploaded purlin/girt workbook.

This module is intentionally separated from Streamlit pages so that future
Column Design logic can be added without changing the UI code.

Units used unless noted otherwise:
- Length, spacing: m
- Loads: kg/m² and kg/m
- Moments: kg-m
- Thickness/dimensions: mm
- Stresses: N/mm² or kg/cm² where noted
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import pi, sqrt
from typing import Dict, Any

E_STEEL_N_PER_MM2 = 205000.0


@dataclass
class LoadInputs:
    span_m: float = 35.5
    bay_spacing_m: float = 9.347
    purlin_or_girt_spacing_m: float = 1.5
    roof_slope_x: float = 10.0
    roof_slope_y: float = 1.0
    dead_load_kg_m2: float = 15.0
    collateral_load_kg_m2: float = 75.0
    live_load_kg_m2: float = 75.0
    wind_load_kg_m2: float = 130.0
    wind_pressure_coeff: float = 1.4
    fy_mpa: float = 345.0
    sag_bars: int = 5


@dataclass
class ZSectionInputs:
    t_mm: float = 2.5
    overall_depth_D_mm: float = 250.0
    b1_mm: float = 64.0
    b2_mm: float = 66.0
    lip1_mm: float = 20.0
    lip2_mm: float = 20.0


@dataclass
class MomentCoefficients:
    span: float
    support: float


PURLIN_END_BAY_COEFF = MomentCoefficients(span=0.0772, support=0.1071)
PURLIN_MID_BAY_COEFF = MomentCoefficients(span=0.0364, support=0.0714)
GIRT_COEFF = MomentCoefficients(span=0.0364, support=0.0714)


def roof_slope_factors(x: float, y: float) -> Dict[str, float]:
    hyp = sqrt(x * x + y * y)
    return {"kx": x / hyp if hyp else 0.0, "ky": y / hyp if hyp else 0.0}


def purlin_loads(inp: LoadInputs) -> Dict[str, Any]:
    f = roof_slope_factors(inp.roof_slope_x, inp.roof_slope_y)
    w_gravity = (inp.dead_load_kg_m2 + inp.live_load_kg_m2 + inp.collateral_load_kg_m2) * inp.purlin_or_girt_spacing_m * f["kx"]
    w_wind = (inp.wind_load_kg_m2 * inp.wind_pressure_coeff - inp.dead_load_kg_m2 * f["kx"]) * inp.purlin_or_girt_spacing_m
    return {
        **f,
        "gravity_load_kg_m": w_gravity,
        "gravity_direction": "DOWNWARD" if w_gravity >= 0 else "UPWARD",
        "wind_net_load_kg_m": w_wind,
        "wind_direction": "UPWARD" if w_wind >= 0 else "DOWNWARD",
    }


def girt_loads(inp: LoadInputs) -> Dict[str, Any]:
    return {
        "dead_load_kg_m": inp.dead_load_kg_m2 * inp.purlin_or_girt_spacing_m,
        "wind_load_kg_m": inp.wind_load_kg_m2 * inp.wind_pressure_coeff * inp.purlin_or_girt_spacing_m,
    }


def purlin_moments(inp: LoadInputs, coeff: MomentCoefficients = PURLIN_END_BAY_COEFF, point_mid_kg_m: float = 0.0, point_support_kg_m: float = 0.0) -> Dict[str, float]:
    l = inp.bay_spacing_m
    loads = purlin_loads(inp)
    return {
        "gravity_span_moment_kg_m": coeff.span * loads["gravity_load_kg_m"] * l * l + point_mid_kg_m,
        "gravity_support_moment_kg_m": coeff.support * loads["gravity_load_kg_m"] * l * l + point_support_kg_m,
        "wind_span_moment_kg_m": coeff.span * loads["wind_net_load_kg_m"] * l * l,
        "wind_support_moment_kg_m": coeff.support * loads["wind_net_load_kg_m"] * l * l,
    }


def girt_moments(inp: LoadInputs, coeff: MomentCoefficients = GIRT_COEFF) -> Dict[str, float]:
    # Spreadsheet uses unbraced length for gravity and bay spacing for wind.
    l_wind = inp.bay_spacing_m
    l_unbraced = inp.bay_spacing_m / (inp.sag_bars + 1) if inp.sag_bars >= 0 else inp.bay_spacing_m
    loads = girt_loads(inp)
    return {
        "unbraced_length_m": l_unbraced,
        "dead_span_moment_kg_m": coeff.span * loads["dead_load_kg_m"] * l_unbraced * l_unbraced,
        "dead_support_moment_kg_m": coeff.support * loads["dead_load_kg_m"] * l_unbraced * l_unbraced,
        "wind_span_moment_kg_m": coeff.span * loads["wind_load_kg_m"] * l_wind * l_wind,
        "wind_support_moment_kg_m": coeff.support * loads["wind_load_kg_m"] * l_wind * l_wind,
    }


def z_section_properties(sec: ZSectionInputs) -> Dict[str, float]:
    """Approximate thin-walled Z-section properties using rectangular parts.

    Matches the workbook intent: web + two flanges + two lips, reported in cm
    units for section modulus/inertia. For final engineering use, verify with
    cold-formed section property software or manufacturer tables.
    """
    t = sec.t_mm
    d = sec.overall_depth_D_mm - 2 * t
    parts = [
        # name, width_x, height_y, centroid_x, centroid_y, area
        ("web", t, d, t / 2, t + d / 2, t * d),
        ("top_flange", sec.b1_mm, t, sec.b1_mm / 2, sec.overall_depth_D_mm - t / 2, sec.b1_mm * t),
        ("bottom_flange", sec.b2_mm, t, sec.b2_mm / 2, t / 2, sec.b2_mm * t),
        ("top_lip", t, max(sec.lip1_mm - t, 0), sec.b1_mm - t / 2, sec.overall_depth_D_mm - t - max(sec.lip1_mm - t, 0) / 2, t * max(sec.lip1_mm - t, 0)),
        ("bottom_lip", t, max(sec.lip2_mm - t, 0), sec.b2_mm - t / 2, t + max(sec.lip2_mm - t, 0) / 2, t * max(sec.lip2_mm - t, 0)),
    ]
    area_mm2 = sum(p[5] for p in parts)
    xbar = sum(p[3] * p[5] for p in parts) / area_mm2
    ybar = sum(p[4] * p[5] for p in parts) / area_mm2
    ixx = 0.0
    iyy = 0.0
    for _, bx, hy, cx, cy, a in parts:
        ixx += bx * hy**3 / 12 + a * (cy - ybar) ** 2
        iyy += hy * bx**3 / 12 + a * (cx - xbar) ** 2
    zxx_top_mm3 = ixx / max(sec.overall_depth_D_mm - ybar, 1e-9)
    zxx_bot_mm3 = ixx / max(ybar, 1e-9)
    zyy_right_mm3 = iyy / max(max(sec.b1_mm, sec.b2_mm) - xbar, 1e-9)
    zyy_left_mm3 = iyy / max(xbar, 1e-9)
    return {
        "d_clear_mm": d,
        "area_cm2": area_mm2 / 100.0,
        "weight_kg_m": 7850.0 * (area_mm2 / 1_000_000.0),
        "xbar_mm": xbar,
        "ybar_mm": ybar,
        "ixx_cm4": ixx / 10000.0,
        "iyy_cm4": iyy / 10000.0,
        "zxx_top_cm3": zxx_top_mm3 / 1000.0,
        "zxx_bottom_cm3": zxx_bot_mm3 / 1000.0,
        "zyy_right_cm3": zyy_right_mm3 / 1000.0,
        "zyy_left_cm3": zyy_left_mm3 / 1000.0,
    }


def code_checks(inp: LoadInputs, sec: ZSectionInputs, props: Dict[str, float], support_moment_kg_m: float, span_moment_kg_m: float) -> Dict[str, Any]:
    fy_kg_cm2 = inp.fy_mpa * 10.1972
    basic_design_stress_n_mm2 = 0.6 * inp.fy_mpa
    overall_depth_ok = sec.overall_depth_D_mm < 150.0 * sec.t_mm
    dmin_mm = max(4.8 * sec.t_mm, (2.8 * sec.t_mm) * ((sec.b1_mm / sec.t_mm) ** 2 - 281200.0 / max(inp.fy_mpa, 1e-9)) if sec.t_mm < 2.1 else 4.8 * sec.t_mm)
    dmin_ok = dmin_mm > 4.8 * sec.t_mm

    z_support_cm3 = 2.0 * min(props["zxx_top_cm3"], props["zxx_bottom_cm3"])
    z_span_cm3 = min(props["zxx_top_cm3"], props["zxx_bottom_cm3"])
    actual_support_n_mm2 = (abs(support_moment_kg_m) * 100.0 / max(z_support_cm3, 1e-9)) * 0.0980665
    actual_span_n_mm2 = (abs(span_moment_kg_m) * 100.0 / max(z_span_cm3, 1e-9)) * 0.0980665
    return {
        "fy_kg_cm2": fy_kg_cm2,
        "basic_design_stress_n_mm2": basic_design_stress_n_mm2,
        "overall_depth_limit_mm": 150.0 * sec.t_mm,
        "overall_depth_ok": overall_depth_ok,
        "minimum_depth_required_mm": dmin_mm,
        "minimum_depth_check_ok": dmin_ok,
        "support_actual_stress_n_mm2": actual_support_n_mm2,
        "span_actual_stress_n_mm2": actual_span_n_mm2,
        "support_stress_ok": actual_support_n_mm2 <= basic_design_stress_n_mm2,
        "span_stress_ok": actual_span_n_mm2 <= basic_design_stress_n_mm2,
    }


def dataclass_to_dict(obj) -> Dict[str, Any]:
    return asdict(obj)
