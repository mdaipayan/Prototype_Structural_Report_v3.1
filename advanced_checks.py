"""Advanced Z-Purlin Design Checks Module

Comprehensive implementation of IS 801:1975 ASD framework including:
- Effective-width reduction analysis
- Lateral-torsional buckling (LTB) checks
- Biaxial bending interaction
- Deflection limits
- Connection design guidance

Units:
- Length, spacing: m
- Loads: kN/m²
- Moments: kN-m
- Stresses: N/mm² (MPa)
- Deflection: mm
"""

from __future__ import annotations
from dataclasses import dataclass
from math import pi, sqrt, cos, sin, radians
from typing import Dict, Any, Tuple


# ============================================================================
# EFFECTIVE-WIDTH REDUCTION ANALYSIS (IS 801:1975 Clause 5.2)
# ============================================================================

def effective_width_factor_web(
    flat_width_ratio: float,
    stress_ratio: float = 1.0,
) -> float:
    """Calculate effective-width reduction factor for unstiffened web (IS 801:1975).
    
    Args:
        flat_width_ratio: h/t (clear web depth / thickness)
        stress_ratio: f/fy (actual stress / yield stress), default 1.0 for elastic
    
    Returns:
        Reduction factor (0 to 1.0)
    """
    lambda_w = flat_width_ratio  # Slenderness ratio
    lambda_p = 60  # Plasticity limit for unstiffened element
    lambda_e = 90 * sqrt(250 / 235)  # Elastic limit (for Fy = 250 MPa reference)
    
    if lambda_w <= lambda_p:
        return 1.0
    elif lambda_p < lambda_w <= lambda_e:
        return (lambda_e - lambda_w) / (lambda_e - lambda_p)
    else:
        return (61000 / (lambda_w**2)) * (stress_ratio)


def effective_width_factor_flange(
    flat_width_ratio: float,
    stress_ratio: float = 1.0,
    edge_stiffener: bool = True,
) -> float:
    """Calculate effective-width reduction factor for flange with edge stiffener.
    
    Args:
        flat_width_ratio: b/t (flange width / thickness)
        stress_ratio: f/fy
        edge_stiffener: True if simple lip stiffener present
    
    Returns:
        Reduction factor (0 to 1.0)
    """
    lambda_f = flat_width_ratio
    
    if edge_stiffener:
        lambda_p = 50  # Plasticity limit with stiffener
        lambda_e = 75 * sqrt(250 / 235)
    else:
        lambda_p = 40
        lambda_e = 60 * sqrt(250 / 235)
    
    if lambda_f <= lambda_p:
        return 1.0
    elif lambda_p < lambda_f <= lambda_e:
        return (lambda_e - lambda_f) / (lambda_e - lambda_p)
    else:
        return (50000 / (lambda_f**2)) * (stress_ratio)


def effective_section_properties(
    gross_properties: Dict[str, float],
    flat_width_checks: Dict[str, float],
    fy_mpa: float = 250.0,
    bending_stress_mpa: float = None,
) -> Dict[str, float]:
    """Calculate effective section properties with width reduction.
    
    Args:
        gross_properties: Section properties (from design_calcs.z_section_properties)
        flat_width_checks: Flat-width ratio results
        fy_mpa: Yield strength
        bending_stress_mpa: Actual bending stress (for non-linear analysis)
    
    Returns:
        Dictionary with effective properties and reduction factors
    """
    if bending_stress_mpa is None:
        bending_stress_mpa = 0.6 * fy_mpa  # Design stress
    
    stress_ratio = min(bending_stress_mpa / fy_mpa, 1.0)
    
    # Calculate reduction factors
    f_web = effective_width_factor_web(flat_width_checks['web_ratio'], stress_ratio)
    f_flange = effective_width_factor_flange(
        flat_width_checks['flange_ratio'],
        stress_ratio,
        edge_stiffener=True
    )
    
    # Apply reductions (simplified - assumes uniform stress distribution)
    reduction_factor = min(f_web, f_flange)  # Conservative approach
    
    return {
        'web_reduction_factor': f_web,
        'flange_reduction_factor': f_flange,
        'combined_reduction_factor': reduction_factor,
        'effective_zxx_cm3': gross_properties['zxx_top_cm3'] * reduction_factor,
        'effective_zyy_cm3': gross_properties['zyy_right_cm3'] * reduction_factor,
        'effective_ixx_cm4': gross_properties['ixx_cm4'] * reduction_factor,
        'effective_iyy_cm4': gross_properties['iyy_cm4'] * reduction_factor,
    }


# ============================================================================
# LATERAL-TORSIONAL BUCKLING (LTB) ANALYSIS (IS 801:1975 Clause 5.4.1)
# ============================================================================

def radius_of_gyration_y(
    section_properties: Dict[str, float],
) -> float:
    """Calculate minor-axis radius of gyration.
    
    Args:
        section_properties: From design_calcs.z_section_properties
    
    Returns:
        ry in cm (minor-axis radius of gyration)
    """
    area_cm2 = section_properties['area_cm2']
    iyy_cm4 = section_properties['iyy_cm4']
    
    if area_cm2 <= 0:
        return 0.0
    
    return sqrt(iyy_cm4 / area_cm2)


def unbraced_length_factor(
    support_condition: str = "continuous",
) -> float:
    """Calculate effective length factor based on support conditions.
    
    Args:
        support_condition: 'continuous' (purlin on bearing), 'simply_supported',
                          'cantilever', 'fixed_both_ends'
    
    Returns:
        Effective length factor K
    """
    factors = {
        'continuous': 0.75,
        'simply_supported': 1.0,
        'fixed_one_end': 0.7,
        'fixed_both_ends': 0.5,
        'cantilever': 2.0,
    }
    return factors.get(support_condition, 1.0)


def slenderness_ratio_ltb(
    unbraced_length_m: float,
    radius_of_gyration_cm: float,
    k_factor: float = 1.0,
) -> float:
    """Calculate slenderness ratio for lateral-torsional buckling.
    
    Args:
        unbraced_length_m: Length without lateral support (m)
        radius_of_gyration_cm: Minor-axis radius of gyration (cm)
        k_factor: Effective length factor (typically 1.0 for purlins)
    
    Returns:
        Slenderness ratio lambda_ltb
    """
    if radius_of_gyration_cm <= 0:
        return 0.0
    
    unbraced_length_cm = unbraced_length_m * 100
    return (k_factor * unbraced_length_cm) / radius_of_gyration_cm


def buckling_stress_ltb(
    slenderness_ratio: float,
    fy_mpa: float = 250.0,
    modulus_e_mpa: float = 205000.0,
) -> Tuple[float, str]:
    """Calculate allowable bending stress considering LTB (IS 801:1975).
    
    Args:
        slenderness_ratio: Lambda for LTB
        fy_mpa: Yield strength (MPa)
        modulus_e_mpa: Modulus of elasticity (MPa)
    
    Returns:
        (Allowable stress in MPa, Failure mode description)
    """
    lambda_c = pi * sqrt(modulus_e_mpa / fy_mpa)  # Critical slenderness ratio
    
    basic_design_stress = 0.6 * fy_mpa
    
    if slenderness_ratio <= 40:
        # Stocky section - no reduction
        return (basic_design_stress, "Stocky - No LTB reduction")
    
    elif 40 < slenderness_ratio <= 60:
        # Intermediate - Linear interpolation
        reduction = (slenderness_ratio - 40) / 20 * 0.2
        allowable = basic_design_stress * (1 - reduction)
        return (allowable, "Intermediate - Linear reduction")
    
    elif 60 < slenderness_ratio <= lambda_c:
        # Elastic - Parabolic reduction
        reduction = (slenderness_ratio / (2 * lambda_c)) ** 2
        allowable = basic_design_stress * (1 - reduction)
        return (allowable, "Elastic - Parabolic reduction")
    
    else:
        # Highly slender - Euler buckling
        allowable = (pi**2 * modulus_e_mpa) / (slenderness_ratio**2)
        return (allowable / 1.67, "Slender - Euler buckling (fs=1.67)")


def ltb_check(
    bending_stress_mpa: float,
    unbraced_length_m: float,
    section_properties: Dict[str, float],
    support_condition: str = "continuous",
    fy_mpa: float = 250.0,
) -> Dict[str, Any]:
    """Comprehensive lateral-torsional buckling check.
    
    Args:
        bending_stress_mpa: Actual bending stress from moment/section modulus
        unbraced_length_m: Length without lateral support
        section_properties: From design_calcs.z_section_properties
        support_condition: Type of support condition
        fy_mpa: Yield strength
    
    Returns:
        Dictionary with LTB check results
    """
    ry = radius_of_gyration_y(section_properties)
    k = unbraced_length_factor(support_condition)
    lambda_ltb = slenderness_ratio_ltb(unbraced_length_m, ry, k)
    
    allowable_stress, failure_mode = buckling_stress_ltb(lambda_ltb, fy_mpa)
    
    return {
        'radius_of_gyration_y_cm': ry,
        'effective_length_factor_k': k,
        'slenderness_ratio_lambda': lambda_ltb,
        'allowable_stress_mpa': allowable_stress,
        'actual_stress_mpa': bending_stress_mpa,
        'utilization_ratio': bending_stress_mpa / max(allowable_stress, 1e-9),
        'is_safe': bending_stress_mpa <= allowable_stress,
        'failure_mode': failure_mode,
        'margin_percent': ((allowable_stress - bending_stress_mpa) / allowable_stress * 100) if allowable_stress > 0 else 0,
    }


# ============================================================================
# BIAXIAL BENDING INTERACTION
# ============================================================================

def biaxial_interaction_check(
    bending_stress_x_mpa: float,
    bending_stress_y_mpa: float,
    allowable_stress_x_mpa: float,
    allowable_stress_y_mpa: float,
    interaction_exponent: float = 1.5,
) -> Dict[str, float]:
    """Check biaxial bending interaction using power law.
    
    Args:
        bending_stress_x_mpa: Major-axis bending stress
        bending_stress_y_mpa: Minor-axis bending stress
        allowable_stress_x_mpa: Major-axis allowable stress
        allowable_stress_y_mpa: Minor-axis allowable stress
        interaction_exponent: Typically 1.5 for cold-formed steel
    
    Returns:
        Dictionary with interaction ratio and safety check
    """
    ratio_x = bending_stress_x_mpa / max(allowable_stress_x_mpa, 1e-9)
    ratio_y = bending_stress_y_mpa / max(allowable_stress_y_mpa, 1e-9)
    
    interaction_ratio = (ratio_x ** interaction_exponent + ratio_y ** interaction_exponent) ** (1 / interaction_exponent)
    
    return {
        'major_axis_utilization': ratio_x,
        'minor_axis_utilization': ratio_y,
        'interaction_ratio': interaction_ratio,
        'is_safe': interaction_ratio <= 1.0,
        'margin_percent': (1 - interaction_ratio) * 100 if interaction_ratio > 0 else 0,
        'governer': 'Major-axis' if ratio_x > ratio_y else 'Minor-axis',
    }


# ============================================================================
# DEFLECTION CHECKS (IS 801:1975 & IS 875)
# ============================================================================

def deflection_limit(
    span_m: float,
    load_type: str = "live",
) -> float:
    """Get deflection limit based on load type and span.
    
    Args:
        span_m: Span of purlin (m)
        load_type: 'dead', 'live', 'wind', 'total'
    
    Returns:
        Maximum allowable deflection in mm
    """
    limits = {
        'dead': span_m * 1000 / 180,      # L/180
        'live': span_m * 1000 / 240,      # L/240
        'wind': span_m * 1000 / 120,      # L/120 (larger deflection acceptable)
        'total': span_m * 1000 / 150,     # L/150 (combined)
    }
    return limits.get(load_type, span_m * 1000 / 240)


def deflection_calculation(
    load_kn_m: float,
    span_m: float,
    modulus_e_mpa: float = 205000.0,
    moment_of_inertia_cm4: float = 100.0,
    support_condition: str = "continuous_span",
) -> float:
    """Calculate maximum deflection for various loading and support conditions.
    
    Args:
        load_kn_m: Distributed load (kN/m)
        span_m: Span length (m)
        modulus_e_mpa: Young's modulus (MPa)
        moment_of_inertia_cm4: Moment of inertia (cm⁴)
        support_condition: 'simply_supported', 'continuous_span', 'fixed_both'
    
    Returns:
        Maximum deflection in mm
    """
    # Convert units. 1 kN/m equals 1 N/mm, so do not multiply by 1000.
    load_n_per_mm = load_kn_m
    span_mm = span_m * 1000
    e_n_mm2 = modulus_e_mpa
    i_mm4 = moment_of_inertia_cm4 * 10000
    
    # Deflection coefficients (w*L⁴ / (C * E * I))
    coefficients = {
        'simply_supported': 5 / 384,
        'continuous_span': 1 / 185,  # Approximate for continuous
        'fixed_both_ends': 1 / 384,
    }
    
    coeff = coefficients.get(support_condition, 1/185)
    
    if i_mm4 <= 0:
        return float('inf')
    
    deflection_mm = (coeff * load_n_per_mm * (span_mm ** 4)) / (e_n_mm2 * i_mm4)
    
    return deflection_mm


def deflection_check(
    load_kn_m: float,
    span_m: float,
    moment_of_inertia_cm4: float,
    load_type: str = "live",
    modulus_e_mpa: float = 205000.0,
    support_condition: str = "continuous_span",
) -> Dict[str, Any]:
    """Comprehensive deflection check.
    
    Args:
        load_kn_m: Distributed load (kN/m)
        span_m: Span (m)
        moment_of_inertia_cm4: Moment of inertia (cm⁴)
        load_type: Type of load for limit determination
        modulus_e_mpa: Young's modulus
        support_condition: Support condition
    
    Returns:
        Dictionary with deflection check results
    """
    actual_deflection = deflection_calculation(
        load_kn_m, span_m, modulus_e_mpa,
        moment_of_inertia_cm4, support_condition
    )
    
    limit_deflection = deflection_limit(span_m, load_type)
    
    return {
        'actual_deflection_mm': actual_deflection,
        'limit_deflection_mm': limit_deflection,
        'utilization_ratio': actual_deflection / limit_deflection,
        'is_safe': actual_deflection <= limit_deflection,
        'margin_mm': limit_deflection - actual_deflection,
        'margin_percent': ((limit_deflection - actual_deflection) / limit_deflection * 100) if limit_deflection > 0 else 0,
    }


# ============================================================================
# CONNECTION DESIGN GUIDANCE
# ============================================================================

@dataclass
class BoltConnection:
    """Bolt connection properties for Z-purlin to frame."""
    bolt_diameter_mm: float = 16.0
    bolt_grade: str = "8.8"  # 8.8, 10.9
    hole_diameter_mm: float = 18.0
    number_of_bolts: int = 2
    bolt_spacing_mm: float = 50.0
    edge_distance_mm: float = 30.0
    end_distance_mm: float = 40.0


def bolt_shear_capacity(
    connection: BoltConnection,
) -> Dict[str, float]:
    """Calculate bolt shear capacity per IS 1367 / IS 800.
    
    Args:
        connection: BoltConnection object with properties
    
    Returns:
        Dictionary with shear capacities
    """
    # Tensile strengths for bolt grades (MPa)
    tensile_strengths = {
        '4.6': 400, '4.8': 400, '5.6': 500, '5.8': 500,
        '6.8': 600, '8.8': 800, '10.9': 1000,
    }
    
    fu = tensile_strengths.get(connection.bolt_grade, 800.0)
    
    # Single bolt area (mm²)
    bolt_area_mm2 = pi * (connection.bolt_diameter_mm / 2) ** 2
    
    # Shear strength (40% of tensile for bearing type, 50% for slip-critical)
    shear_strength_bearing = 0.40 * fu
    shear_strength_friction = 0.50 * fu
    
    # Capacity per bolt (kN)
    capacity_bearing = (bolt_area_mm2 * shear_strength_bearing) / 1000
    capacity_friction = (bolt_area_mm2 * shear_strength_friction) / 1000
    
    # Total capacity
    total_capacity_bearing = capacity_bearing * connection.number_of_bolts
    total_capacity_friction = capacity_friction * connection.number_of_bolts
    
    return {
        'bolt_diameter_mm': connection.bolt_diameter_mm,
        'bolt_grade': connection.bolt_grade,
        'tensile_strength_mpa': fu,
        'shear_strength_bearing_mpa': shear_strength_bearing,
        'single_bolt_area_mm2': bolt_area_mm2,
        'capacity_per_bolt_kn': capacity_bearing,
        'capacity_per_bolt_friction_kn': capacity_friction,
        'total_capacity_bearing_kn': total_capacity_bearing,
        'total_capacity_friction_kn': total_capacity_friction,
        'number_of_bolts': connection.number_of_bolts,
    }


def bearing_capacity_purlin(
    connection: BoltConnection,
    material_thickness_mm: float = 2.5,
    fy_mpa: float = 250.0,
) -> Dict[str, float]:
    """Calculate bearing capacity of purlin material under bolt.
    
    Args:
        connection: BoltConnection object
        material_thickness_mm: Thickness of purlin (mm)
        fy_mpa: Yield strength of purlin (MPa)
    
    Returns:
        Dictionary with bearing capacity results
    """
    # Bearing capacity = 1.5 * fu * d * t (conservative)
    fu_purlin_mpa = 1.2 * fy_mpa  # Approximate ultimate for cold-formed
    
    bearing_stress_mpa = 1.5 * fu_purlin_mpa
    
    # Capacity per bolt
    capacity_per_bolt_kn = (bearing_stress_mpa * connection.bolt_diameter_mm * material_thickness_mm) / 1000
    
    # Total for all bolts
    total_bearing_capacity_kn = capacity_per_bolt_kn * connection.number_of_bolts
    
    bolt_capacity = bolt_shear_capacity(connection)

    return {
        'tensile_strength_purlin_mpa': fu_purlin_mpa,
        'bearing_stress_limit_mpa': bearing_stress_mpa,
        'capacity_per_bolt_kn': capacity_per_bolt_kn,
        'total_bearing_capacity_kn': total_bearing_capacity_kn,
        'governing_mode': 'Bolt shear' if bolt_capacity['total_capacity_bearing_kn'] < total_bearing_capacity_kn else 'Bearing',
    }


def connection_check(
    shear_force_kn: float,
    connection: BoltConnection,
    purlin_thickness_mm: float = 2.5,
    fy_mpa: float = 250.0,
) -> Dict[str, Any]:
    """Comprehensive connection design check.
    
    Args:
        shear_force_kn: Design shear force (kN)
        connection: BoltConnection configuration
        purlin_thickness_mm: Thickness of purlin web
        fy_mpa: Yield strength
    
    Returns:
        Dictionary with connection check results
    """
    bolt_capacity = bolt_shear_capacity(connection)
    bearing_capacity = bearing_capacity_purlin(connection, purlin_thickness_mm, fy_mpa)
    
    # Governing capacity
    governing_capacity = min(
        bolt_capacity['total_capacity_bearing_kn'],
        bearing_capacity['total_bearing_capacity_kn']
    )
    
    return {
        'design_shear_kn': shear_force_kn,
        'bolt_shear_capacity_kn': bolt_capacity['total_capacity_bearing_kn'],
        'bearing_capacity_kn': bearing_capacity['total_bearing_capacity_kn'],
        'governing_capacity_kn': governing_capacity,
        'utilization_ratio': shear_force_kn / max(governing_capacity, 1e-9),
        'is_safe': shear_force_kn <= governing_capacity,
        'margin_kn': governing_capacity - shear_force_kn,
        'margin_percent': ((governing_capacity - shear_force_kn) / governing_capacity * 100) if governing_capacity > 0 else 0,
        'governing_mode': 'Bolt shear' if bolt_capacity['total_capacity_bearing_kn'] < bearing_capacity['total_bearing_capacity_kn'] else 'Bearing',
        'bolt_details': bolt_capacity,
    }
