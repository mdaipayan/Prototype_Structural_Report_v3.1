"""Advanced Z-Purlin Design Calculations

Comprehensive analysis including:
- Effective-width reduction (IS 801:1975 Clause 5.3)
- Lateral-torsional buckling (LTB) checks
- Biaxial bending interaction
- Deflection analysis
- Connection design considerations

Units: kN, m, mm, N/mm², kg/cm²
"""

from __future__ import annotations
from dataclasses import dataclass
from math import cos, radians, sin, sqrt, pi
from typing import Dict, Any, Tuple

# Constants
E_STEEL_N_PER_MM2 = 205000.0
MPA_TO_KG_PER_CM2 = 10.1972
KG_PER_CM2_TO_N_PER_MM2 = 0.0980665
G_STEEL = 79000.0  # N/mm² (Shear modulus)


@dataclass
class EffectiveWidthResult:
    """Results of effective-width reduction analysis."""
    web_flat_width_mm: float
    flange_flat_width_mm: float
    web_stress_ratio: float
    flange_stress_ratio: float
    web_effective_width_mm: float
    flange_effective_width_mm: float
    reduction_factor_web: float
    reduction_factor_flange: float
    effective_section_area_cm2: float
    effective_moment_of_inertia_cm4: float
    effective_section_modulus_cm3: float


def effective_width_reduction(
    fy_mpa: float,
    flat_width_mm: float,
    thickness_t_mm: float,
    actual_stress_n_mm2: float,
    element_type: str = "web"  # "web" or "flange"
) -> Dict[str, float]:
    """
    Calculate effective-width reduction per IS 801:1975 Clause 5.3.
    
    For cold-formed members:
    - Web (interior element): k = 0.43 (simply supported)
    - Flange (edge stiffened): k = 0.95 (simply supported with simple lip)
    
    Critical stress = k*π²*E / (12*(1-ν²)) / (b/t)²
    where ν = 0.3 for steel
    
    Effective width = b * sqrt(λ_c) / λ_p  (for λ_p > 0.673)
    """
    
    fy_kg_cm2 = fy_mpa * MPA_TO_KG_PER_CM2
    stress_ratio = actual_stress_n_mm2 / fy_mpa  # Ratio of actual to yield stress
    
    # Plate buckling coefficients (IS 801:1975)
    if element_type == "web":
        k_coefficient = 0.43  # Simply supported interior element
    elif element_type == "flange":
        k_coefficient = 0.95  # Edge stiffened with simple lip
    else:
        k_coefficient = 0.43
    
    # Buckling stress (in N/mm²)
    nu = 0.3  # Poisson's ratio for steel
    slenderness_ratio = flat_width_mm / max(thickness_t_mm, 1e-9)
    
    # Critical buckling stress
    fcr_n_mm2 = (k_coefficient * pi**2 * E_STEEL_N_PER_MM2) / (12 * (1 - nu**2)) / (slenderness_ratio**2)
    
    # Plate slenderness parameter
    lambda_p = sqrt(fy_mpa / max(fcr_n_mm2, 1e-9))
    
    # Effective width calculation
    if lambda_p <= 0.673:
        # No reduction needed
        b_eff_mm = flat_width_mm
        reduction_factor = 1.0
    else:
        # Linear reduction: IS 801:1975
        reduction_factor = (0.673 / lambda_p) if lambda_p > 0 else 1.0
        b_eff_mm = flat_width_mm * reduction_factor
    
    return {
        "flat_width_mm": flat_width_mm,
        "thickness_mm": thickness_t_mm,
        "slenderness_ratio": slenderness_ratio,
        "critical_stress_n_mm2": fcr_n_mm2,
        "plate_slenderness_lambda": lambda_p,
        "actual_stress_n_mm2": actual_stress_n_mm2,
        "stress_ratio": stress_ratio,
        "effective_width_mm": b_eff_mm,
        "reduction_factor": reduction_factor,
        "element_type": element_type,
    }


def lateral_torsional_buckling(
    fy_mpa: float,
    moment_kn_m: float,
    section_modulus_cm3: float,
    unbraced_length_m: float,
    section_depth_mm: float,
    flange_width_mm: float,
    thickness_t_mm: float,
) -> Dict[str, Any]:
    """
    Lateral-torsional buckling (LTB) check per IS 801:1975 Clause 5.8.1.
    
    For rolled sections and cold-formed members without lateral support.
    Cb = 1.0 (conservative for intermediate loads)
    """
    
    # Basic design stress
    fb = 0.6 * fy_mpa  # Allowable bending stress (N/mm²)
    
    # Convert moment to stress
    actual_stress_n_mm2 = (abs(moment_kn_m) * 100.0 / max(section_modulus_cm3, 1e-9)) * KG_PER_CM2_TO_N_PER_MM2
    
    # Unbraced length to depth ratio
    lu_d_ratio = (unbraced_length_m * 1000) / section_depth_mm
    
    # Torsional constant approximation for Z-section
    # J ≈ (1/3) * sum(b_i * t_i³) for thin-walled sections
    j_constant = (1/3) * (2 * flange_width_mm * thickness_t_mm**3 + 
                          (section_depth_mm - 2*thickness_t_mm) * thickness_t_mm**3)
    
    # Warping constant (approximate for lipped Z)
    c_w = (section_depth_mm**2 * (flange_width_mm - thickness_t_mm)**2 * thickness_t_mm) / 24
    
    # Critical moment (elastic)
    ry_mm = sqrt((2 * flange_width_mm * thickness_t_mm**3) / 12 / (2 * flange_width_mm * thickness_t_mm))  # Radius of gyration about minor axis
    
    # Simplified LTB check: Allowable stress reduction
    # For unbraced length parameter rL = (Lu/ry) * sqrt(fy/E)
    r_l = (unbraced_length_m * 1000 / max(ry_mm, 1e-9)) * sqrt(fy_mpa / E_STEEL_N_PER_MM2)
    
    # Allowable stress coefficient
    if r_l <= 0.2:
        cb_factor = 1.0
    elif r_l <= 1.0:
        cb_factor = 1.0 - 0.4 * (r_l - 0.2) / 0.8
    else:
        cb_factor = 0.6 / r_l
    
    # Adjusted allowable stress
    f_allow = fb * cb_factor
    
    # Check
    ltb_ok = actual_stress_n_mm2 <= f_allow
    ratio = actual_stress_n_mm2 / f_allow if f_allow > 0 else 0
    
    return {
        "unbraced_length_m": unbraced_length_m,
        "section_depth_mm": section_depth_mm,
        "lu_d_ratio": lu_d_ratio,
        "radius_of_gyration_ry_mm": ry_mm,
        "r_l_parameter": r_l,
        "basic_allowable_stress_n_mm2": fb,
        "cb_reduction_factor": cb_factor,
        "adjusted_allowable_stress_n_mm2": f_allow,
        "actual_stress_n_mm2": actual_stress_n_mm2,
        "stress_ratio": ratio,
        "ltb_ok": ltb_ok,
        "torsional_constant_mm4": j_constant,
        "warping_constant_mm6": c_w,
    }


def biaxial_bending_interaction(
    moment_x_kn_m: float,
    moment_y_kn_m: float,
    section_modulus_x_cm3: float,
    section_modulus_y_cm3: float,
    fy_mpa: float,
    allow_stress_n_mm2: float,
) -> Dict[str, Any]:
    """
    Biaxial bending interaction check per IS 801:1975 Clause 5.5.2.
    
    Combined stress check:
    (fb_x / Fb) + (fb_y / Fb) ≤ 1.0  (Linear interaction)
    
    Or more accurate:
    (fb_x / Fb)^m + (fb_y / Fb)^m ≤ 1.0  where m = 1.5 to 2.0
    """
    
    # Calculate stresses
    fb_x = (abs(moment_x_kn_m) * 100.0 / max(section_modulus_x_cm3, 1e-9)) * KG_PER_CM2_TO_N_PER_MM2
    fb_y = (abs(moment_y_kn_m) * 100.0 / max(section_modulus_y_cm3, 1e-9)) * KG_PER_CM2_TO_N_PER_MM2
    
    # Stress ratios
    ratio_x = fb_x / max(allow_stress_n_mm2, 1e-9)
    ratio_y = fb_y / max(allow_stress_n_mm2, 1e-9)
    
    # Linear interaction check
    interaction_linear = ratio_x + ratio_y
    
    # Non-linear interaction (Eurocode approach, m=1.5)
    m = 1.5
    interaction_nonlinear = ratio_x**m + ratio_y**m
    
    # Quadratic interaction (m=2)
    interaction_quadratic = ratio_x**2 + ratio_y**2
    
    # Most conservative: linear
    biaxial_ok = interaction_linear <= 1.0
    
    return {
        "moment_x_kn_m": moment_x_kn_m,
        "moment_y_kn_m": moment_y_kn_m,
        "stress_x_n_mm2": fb_x,
        "stress_y_n_mm2": fb_y,
        "allowable_stress_n_mm2": allow_stress_n_mm2,
        "stress_ratio_x": ratio_x,
        "stress_ratio_y": ratio_y,
        "interaction_linear": interaction_linear,
        "interaction_nonlinear": interaction_nonlinear,
        "interaction_quadratic": interaction_quadratic,
        "biaxial_ok": biaxial_ok,
        "governing_ratio": max(interaction_linear, 0),
    }


def deflection_analysis(
    moment_kn_m: float,
    span_m: float,
    moment_of_inertia_cm4: float,
    load_kn_m: float,
    load_type: str = "distributed"
) -> Dict[str, Any]:
    """
    Deflection analysis per IS 801:1975 Clause 6.2.
    
    Typical limits:
    - Roof members: L/180 to L/240
    - Floor members: L/240 to L/360
    """
    
    # Moment of inertia in mm⁴
    i_mm4 = moment_of_inertia_cm4 * 10000
    
    # Deflection formula: δ = (5*w*L⁴) / (384*E*I)  for distributed load
    # δ = (P*L³) / (48*E*I)  for point load at mid-span
    
    e_n_mm2 = E_STEEL_N_PER_MM2
    l_mm = span_m * 1000
    
    if load_type == "distributed":
        # Distributed load: w in kN/m, convert to N/mm
        w_n_mm = load_kn_m / 1000
        delta_mm = (5 * w_n_mm * (l_mm**4)) / (384 * e_n_mm2 * i_mm4)
    else:
        # Point load at mid-span
        p_n = load_kn_m * 1000
        delta_mm = (p_n * (l_mm**3)) / (48 * e_n_mm2 * i_mm4)
    
    # Deflection limits
    limits = {
        "roof_steep": span_m / 180,  # L/180
        "roof_normal": span_m / 240,  # L/240
        "floor_normal": span_m / 240,  # L/240
        "floor_sensitive": span_m / 360,  # L/360
    }
    
    # Check against limits
    checks = {
        "roof_steep": delta_mm <= limits["roof_steep"] * 1000,
        "roof_normal": delta_mm <= limits["roof_normal"] * 1000,
        "floor_normal": delta_mm <= limits["floor_normal"] * 1000,
        "floor_sensitive": delta_mm <= limits["floor_sensitive"] * 1000,
    }
    
    return {
        "span_m": span_m,
        "load_kn_m": load_kn_m,
        "load_type": load_type,
        "moment_of_inertia_cm4": moment_of_inertia_cm4,
        "deflection_mm": delta_mm,
        "deflection_ratio": delta_mm / (span_m * 1000) if span_m > 0 else 0,
        "limits_mm": {k: v * 1000 for k, v in limits.items()},
        "limit_checks": checks,
    }


def connection_design_considerations(
    purlin_spacing_m: float,
    purlin_load_kn_m: float,
    section_area_cm2: float,
    flange_width_mm: float,
    thickness_t_mm: float,
    fy_mpa: float,
) -> Dict[str, Any]:
    """
    Connection design considerations and recommendations.
    
    Includes:
    - Fastener requirements
    - Bearing area calculations
    - Shear lag effects
    - Hole requirements
    """
    
    # Reaction force at support
    reaction_kn = purlin_spacing_m * purlin_load_kn_m / 2
    
    # Fastener requirements
    # Typical self-drilling screws: #10-16 with capacities 2-8 kN per screw
    fasteners_required = int(reaction_kn / 4.0) + 1  # Assuming 4 kN per fastener
    
    # Bearing area on support structure
    # Effective bearing length (typically 50-100 mm for web connection)
    bearing_length_mm = 80.0
    bearing_area_mm2 = bearing_length_mm * thickness_t_mm
    
    # Bearing stress (conservative limit: 0.9*Fy)
    bearing_stress_allowed_n_mm2 = 0.9 * fy_mpa
    bearing_capacity_kn = (bearing_area_mm2 * bearing_stress_allowed_n_mm2) / 1000
    
    # Shear lag reduction (if applicable)
    shear_lag_factor = 0.85  # Typical for bolted connections
    
    # Block shear strength consideration
    # Critical shear path length for web connection
    shear_path_mm = bearing_length_mm
    shear_area_mm2 = shear_path_mm * thickness_t_mm
    fv = 0.4 * fy_mpa  # Allowable shear stress
    shear_capacity_kn = (shear_area_mm2 * fv) / 1000
    
    return {
        "reaction_force_kn": reaction_kn,
        "fasteners_required": fasteners_required,
        "fastener_spacing_mm": 50,  # Typical spacing
        "bearing_length_mm": bearing_length_mm,
        "bearing_area_mm2": bearing_area_mm2,
        "bearing_stress_allowed_n_mm2": bearing_stress_allowed_n_mm2,
        "bearing_capacity_kn": bearing_capacity_kn,
        "bearing_ok": reaction_kn <= bearing_capacity_kn,
        "shear_lag_factor": shear_lag_factor,
        "shear_area_mm2": shear_area_mm2,
        "shear_stress_allowed_n_mm2": fv,
        "shear_capacity_kn": shear_capacity_kn,
        "shear_ok": reaction_kn <= shear_capacity_kn,
        "connection_notes": [
            "Use self-drilling screws #10-16 or equivalent bolts",
            "Maintain minimum 1.5*d spacing between fasteners",
            "Maintain minimum 1.5*d edge distance",
            "Consider high-strength fasteners for critical connections",
            "Provide backing plates if bearing on weak substrate",
            "Check support structure capacity",
        ]
    }


def comprehensive_design_check(
    fy_mpa: float,
    span_m: float,
    spacing_m: float,
    slope_deg: float,
    depth_h_mm: float,
    flange_b_mm: float,
    lip_d_mm: float,
    thickness_t_mm: float,
    dead_load_kn_m2: float,
    live_load_kn_m2: float,
    wind_load_kn_m2: float,
    moment_x_kn_m: float,
    moment_y_kn_m: float,
    moment_of_inertia_x_cm4: float,
    moment_of_inertia_y_cm4: float,
    section_modulus_x_cm3: float,
    section_modulus_y_cm3: float,
    section_area_cm2: float,
    unbraced_length_m: float = None,
) -> Dict[str, Any]:
    """
    Comprehensive design check combining all analysis methods.
    Returns combined design adequacy assessment.
    """
    
    if unbraced_length_m is None:
        unbraced_length_m = span_m
    
    # Basic allowable stress
    fb = 0.6 * fy_mpa
    
    # Stress calculations
    stress_x = (abs(moment_x_kn_m) * 100.0 / max(section_modulus_x_cm3, 1e-9)) * KG_PER_CM2_TO_N_PER_MM2
    stress_y = (abs(moment_y_kn_m) * 100.0 / max(section_modulus_y_cm3, 1e-9)) * KG_PER_CM2_TO_N_PER_MM2
    
    # 1. Effective width check
    eff_width_x = effective_width_reduction(fy_mpa, depth_h_mm - 2*thickness_t_mm, 
                                            thickness_t_mm, stress_x, "web")
    eff_width_y = effective_width_reduction(fy_mpa, flange_b_mm - 2*thickness_t_mm, 
                                            thickness_t_mm, stress_y, "flange")
    
    # 2. LTB check
    ltb_check = lateral_torsional_buckling(fy_mpa, moment_x_kn_m, section_modulus_x_cm3,
                                          unbraced_length_m, depth_h_mm, flange_b_mm, thickness_t_mm)
    
    # 3. Biaxial bending
    biaxial_check = biaxial_bending_interaction(moment_x_kn_m, moment_y_kn_m, 
                                               section_modulus_x_cm3, section_modulus_y_cm3,
                                               fy_mpa, ltb_check["adjusted_allowable_stress_n_mm2"])
    
    # 4. Deflection check
    gravity_load = (dead_load_kn_m2 + live_load_kn_m2) * spacing_m
    deflection_check = deflection_analysis(moment_x_kn_m, span_m, moment_of_inertia_x_cm4, 
                                          gravity_load, "distributed")
    
    # 5. Connection design
    connection_check = connection_design_considerations(spacing_m, gravity_load, section_area_cm2,
                                                       flange_b_mm, thickness_t_mm, fy_mpa)
    
    # Overall assessment
    all_ok = (eff_width_x["reduction_factor"] > 0 and 
              eff_width_y["reduction_factor"] > 0 and
              ltb_check["ltb_ok"] and
              biaxial_check["biaxial_ok"] and
              deflection_check["limit_checks"]["roof_normal"] and
              connection_check["bearing_ok"] and
              connection_check["shear_ok"])
    
    return {
        "effective_width_web": eff_width_x,
        "effective_width_flange": eff_width_y,
        "lateral_torsional_buckling": ltb_check,
        "biaxial_bending": biaxial_check,
        "deflection": deflection_check,
        "connection": connection_check,
        "design_adequate": all_ok,
        "governing_ratio": max(
            eff_width_x["reduction_factor"],
            eff_width_y["reduction_factor"],
            ltb_check["stress_ratio"],
            biaxial_check["governing_ratio"],
            max(deflection_check["limit_checks"].values())
        ),
    }
