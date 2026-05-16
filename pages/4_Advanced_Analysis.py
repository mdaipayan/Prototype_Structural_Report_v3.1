"""Streamlit Advanced Z-Purlin Design Analysis Page

Comprehensive design checks including:
- Effective-width reduction
- Lateral-torsional buckling
- Biaxial bending interaction
- Deflection verification
- Connection design
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from design_calcs import (
    ZPurlinASDInputs, z_purlin_flat_width_checks, z_purlin_resolved_loads,
    z_purlin_design_moments, z_section_properties, ZSectionInputs,
    bending_stress_n_mm2
)
from advanced_checks import (
    effective_section_properties, ltb_check, biaxial_interaction_check,
    deflection_check, BoltConnection, connection_check, deflection_limit
)

st.set_page_config(page_title="Advanced Z-Purlin Design", layout="wide")

st.title("🔬 Advanced Z-Purlin Design Analysis")
st.caption("Complete IS 801:1975 design verification with LTB, biaxial interaction, deflection & connections")

# Tabs for organized workflow
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Effective-Width", "LTB Analysis", "Biaxial Check", "Deflection", "Connections"
])

# Initialize session state
if "adv_inputs" not in st.session_state:
    st.session_state.adv_inputs = ZPurlinASDInputs()
if "adv_section" not in st.session_state:
    st.session_state.adv_section = ZSectionInputs()

# Sidebar for base inputs (shared across tabs)
st.sidebar.header("📐 Base Design Inputs")

# Material & Geometry
fy_mpa = st.sidebar.number_input(
    "Fy (MPa)", min_value=200.0, max_value=450.0,
    value=st.session_state.adv_inputs.fy_mpa, step=10.0
)
span_m = st.sidebar.number_input(
    "Span (m)", min_value=1.0, max_value=15.0,
    value=st.session_state.adv_inputs.span_m, step=0.5
)
spacing_m = st.sidebar.number_input(
    "Spacing (m)", min_value=0.5, max_value=3.0,
    value=st.session_state.adv_inputs.spacing_m, step=0.1
)
slope_deg = st.sidebar.number_input(
    "Slope (°)", min_value=0.0, max_value=45.0,
    value=st.session_state.adv_inputs.slope_deg, step=1.0
)

# Section properties
st.sidebar.subheader("Z-Section Dims")
h_mm = st.sidebar.number_input(
    "h (mm)", min_value=100.0, max_value=400.0,
    value=st.session_state.adv_section.overall_depth_D_mm, step=10.0
)
b_mm = st.sidebar.number_input(
    "b (mm)", min_value=40.0, max_value=120.0,
    value=st.session_state.adv_section.b1_mm, step=5.0
)
d_mm = st.sidebar.number_input(
    "d (mm)", min_value=10.0, max_value=40.0,
    value=st.session_state.adv_section.lip1_mm, step=2.0
)
t_mm = st.sidebar.number_input(
    "t (mm)", min_value=1.2, max_value=4.0,
    value=st.session_state.adv_section.t_mm, step=0.2
)

# Loads
st.sidebar.subheader("Service Loads")
dl = st.sidebar.number_input(
    "DL (kN/m²)", min_value=0.0, max_value=2.0,
    value=st.session_state.adv_inputs.dead_load_kn_m2, step=0.05, format="%.3f"
)
ll = st.sidebar.number_input(
    "LL (kN/m²)", min_value=0.0, max_value=2.0,
    value=st.session_state.adv_inputs.live_load_kn_m2, step=0.05, format="%.3f"
)
wl = st.sidebar.number_input(
    "WL (kN/m²)", min_value=-3.0, max_value=0.0,
    value=st.session_state.adv_inputs.wind_load_kn_m2, step=0.05, format="%.3f"
)

# Update session state
st.session_state.adv_inputs.fy_mpa = fy_mpa
st.session_state.adv_inputs.span_m = span_m
st.session_state.adv_inputs.spacing_m = spacing_m
st.session_state.adv_inputs.slope_deg = slope_deg
st.session_state.adv_inputs.dead_load_kn_m2 = dl
st.session_state.adv_inputs.live_load_kn_m2 = ll
st.session_state.adv_inputs.wind_load_kn_m2 = wl

st.session_state.adv_section.overall_depth_D_mm = h_mm
st.session_state.adv_section.b1_mm = b_mm
st.session_state.adv_section.b2_mm = b_mm
st.session_state.adv_section.lip1_mm = d_mm
st.session_state.adv_section.lip2_mm = d_mm
st.session_state.adv_section.t_mm = t_mm

# Calculate base properties
checks = z_purlin_flat_width_checks(st.session_state.adv_inputs)
loads = z_purlin_resolved_loads(st.session_state.adv_inputs)
moments = z_purlin_design_moments(st.session_state.adv_inputs, loads)
section_props = z_section_properties(st.session_state.adv_section)

# ========================================================================
# TAB 1: EFFECTIVE-WIDTH REDUCTION
# ========================================================================
with tab1:
    st.header("1️⃣ Effective-Width Reduction Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Preliminary Checks")
        st.write(f"**Web h/t ratio:** {checks['web_ratio']:.1f} (limit: {checks['web_ratio_limit']:.0f})")
        st.write(f"**Flange b/t ratio:** {checks['flange_ratio']:.1f} (limit: {checks['flange_ratio_limit']:.0f})")
        
        # Design stress
        design_stress_mpa = 0.6 * fy_mpa
        bending_stress_x = bending_stress_n_mm2(
            moments['gravity_major_axis_kn_m'] * 100,
            section_props['zxx_top_cm3']
        )
        
        st.write(f"**Design Stress (0.6Fy):** {design_stress_mpa:.1f} MPa")
        st.write(f"**Actual Bending Stress:** {bending_stress_x:.1f} MPa")
    
    with col2:
        st.subheader("Stress Ratio")
        stress_ratio = bending_stress_x / max(design_stress_mpa, 1e-9)
        st.metric("f/fy", f"{stress_ratio:.3f}")
    
    # Calculate effective properties
    eff_props = effective_section_properties(
        section_props, checks, fy_mpa, bending_stress_x
    )
    
    st.subheader("Effective-Width Reduction Factors")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Web Reduction", f"{eff_props['web_reduction_factor']:.3f}")
    with col2:
        st.metric("Flange Reduction", f"{eff_props['flange_reduction_factor']:.3f}")
    with col3:
        st.metric("Combined", f"{eff_props['combined_reduction_factor']:.3f}")
    
    # Effective section moduli
    st.subheader("Effective Section Properties")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Major-Axis (Zxx)**")
        st.metric("Gross", f"{section_props['zxx_top_cm3']:.2f} cm³")
        st.metric("Effective", f"{eff_props['effective_zxx_cm3']:.2f} cm³")
        reduction_pct = (1 - eff_props['combined_reduction_factor']) * 100
        st.write(f"*Reduction: {reduction_pct:.1f}%*")
    
    with col2:
        st.write("**Minor-Axis (Zyy)**")
        st.metric("Gross", f"{section_props['zyy_right_cm3']:.2f} cm³")
        st.metric("Effective", f"{eff_props['effective_zyy_cm3']:.2f} cm³")

# ========================================================================
# TAB 2: LATERAL-TORSIONAL BUCKLING
# ========================================================================
with tab2:
    st.header("2️⃣ Lateral-Torsional Buckling (LTB) Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        unbraced_length_m = st.number_input(
            "Unbraced Length (m)", min_value=0.1, max_value=span_m,
            value=span_m / 2, step=0.5
        )
        support_condition = st.selectbox(
            "Support Condition",
            ["continuous", "simply_supported", "fixed_one_end", "fixed_both_ends", "cantilever"]
        )
    
    with col2:
        st.write("**Support Condition Factors:**")
        st.write("• Continuous: K = 0.75")
        st.write("• Simply supported: K = 1.0")
        st.write("• Fixed-One: K = 0.7")
        st.write("• Fixed-Both: K = 0.5")
        st.write("• Cantilever: K = 2.0")
    
    # LTB Check
    ltb_result = ltb_check(
        bending_stress_x, unbraced_length_m, section_props,
        support_condition, fy_mpa
    )
    
    st.subheader("LTB Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Radius of Gyration (ry)",
            f"{ltb_result['radius_of_gyration_y_cm']:.2f} cm"
        )
    with col2:
        st.metric(
            "Slenderness Ratio (λ)",
            f"{ltb_result['slenderness_ratio_lambda']:.1f}"
        )
    with col3:
        st.metric(
            "Failure Mode",
            ltb_result['failure_mode'],
            delta=f"Margin: {ltb_result['margin_percent']:.1f}%"
        )
    
    # Allowable stress
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Allowable Bending Stress",
            f"{ltb_result['allowable_stress_mpa']:.1f} MPa"
        )
    with col2:
        st.metric(
            "Actual Bending Stress",
            f"{ltb_result['actual_stress_mpa']:.1f} MPa"
        )
    
    # Safety status
    if ltb_result['is_safe']:
        st.success(f"✅ LTB SAFE - Utilization: {ltb_result['utilization_ratio']:.1%}")
    else:
        st.error(f"❌ LTB CRITICAL - Utilization: {ltb_result['utilization_ratio']:.1%}")

# ========================================================================
# TAB 3: BIAXIAL BENDING INTERACTION
# ========================================================================
with tab3:
    st.header("3️⃣ Biaxial Bending Interaction Check")
    
    # Calculate minor-axis stress
    bending_stress_y = bending_stress_n_mm2(
        moments['gravity_minor_axis_kn_m'] * 100,
        section_props['zyy_right_cm3']
    )
    
    # For this analysis, use same allowable stress for both axes (simplified)
    allowable_major = 0.6 * fy_mpa
    allowable_minor = 0.6 * fy_mpa
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Major Axis (Normal Loading)**")
        st.metric("Actual Stress", f"{bending_stress_x:.2f} MPa")
        st.metric("Allowable Stress", f"{allowable_major:.2f} MPa")
        st.metric("Utilization", f"{bending_stress_x/allowable_major:.1%}")
    
    with col2:
        st.write("**Minor Axis (Tangential Loading)**")
        st.metric("Actual Stress", f"{bending_stress_y:.2f} MPa")
        st.metric("Allowable Stress", f"{allowable_minor:.2f} MPa")
        st.metric("Utilization", f"{bending_stress_y/allowable_minor:.1%}")
    
    # Interaction check
    interaction = biaxial_interaction_check(
        bending_stress_x, bending_stress_y,
        allowable_major, allowable_minor,
        interaction_exponent=1.5
    )
    
    st.subheader("Interaction Ratio")
    st.metric(
        "Combined Interaction Ratio",
        f"{interaction['interaction_ratio']:.3f}",
        delta=f"Margin: {interaction['margin_percent']:.1f}%"
    )
    
    st.write(f"**Governer:** {interaction['governer']} axis")
    
    if interaction['is_safe']:
        st.success(f"✅ BIAXIAL CHECK PASSED")
    else:
        st.error(f"❌ BIAXIAL CHECK FAILED")

# ========================================================================
# TAB 4: DEFLECTION VERIFICATION
# ========================================================================
with tab4:
    st.header("4️⃣ Deflection Verification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        load_type = st.radio(
            "Select Load Case",
            ["Dead Load (DL)", "Live Load (LL)", "Wind Load (WL)", "Total (DL+LL)"],
            index=1
        )
    
    with col2:
        support_type = st.selectbox(
            "Support Condition",
            ["simply_supported", "continuous_span", "fixed_both_ends"]
        )
    
    # Select appropriate load
    load_map = {
        "Dead Load (DL)": loads['dead_line_load_kn_m'],
        "Live Load (LL)": loads['live_line_load_kn_m'],
        "Wind Load (WL)": abs(loads['wind_line_load_kn_m']),
        "Total (DL+LL)": loads['gravity_line_load_kn_m'],
    }
    
    selected_load = load_map[load_type]
    
    # Deflection check
    defl_result = deflection_check(
        selected_load, span_m, section_props['ixx_cm4'],
        load_type=load_type.split()[0].lower(),
        support_condition=support_type
    )
    
    st.subheader("Deflection Results")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Actual Deflection",
            f"{defl_result['actual_deflection_mm']:.2f} mm"
        )
    with col2:
        st.metric(
            "Allowable Deflection",
            f"{defl_result['limit_deflection_mm']:.2f} mm"
        )
    with col3:
        st.metric(
            "L/Ratio",
            f"L/{span_m*1000/defl_result['actual_deflection_mm']:.0f}" if defl_result['actual_deflection_mm'] > 0 else "∞"
        )
    
    # Safety status
    if defl_result['is_safe']:
        st.success(f"✅ DEFLECTION SAFE - Margin: {defl_result['margin_percent']:.1f}%")
    else:
        st.warning(f"⚠️ DEFLECTION CRITICAL - Over limit by: {abs(defl_result['margin_mm']):.2f} mm")

# ========================================================================
# TAB 5: CONNECTION DESIGN
# ========================================================================
with tab5:
    st.header("5️⃣ Connection Design & Verification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Bolt Configuration")
        bolt_dia = st.number_input("Bolt Diameter (mm)", 12.0, 24.0, 16.0, step=2.0)
        bolt_grade = st.selectbox("Bolt Grade", ["4.6", "4.8", "5.6", "5.8", "6.8", "8.8", "10.9"], index=5)
        num_bolts = st.number_input("Number of Bolts", 1, 6, 2)
    
    with col2:
        st.subheader("Connection Type")
        hole_dia = st.number_input("Hole Diameter (mm)", 12.0, 30.0, bolt_dia + 2, step=1.0)
        edge_dist = st.number_input("Edge Distance (mm)", 20.0, 60.0, 30.0, step=5.0)
        end_dist = st.number_input("End Distance (mm)", 20.0, 80.0, 40.0, step=5.0)
    
    # Create connection object
    conn = BoltConnection(
        bolt_diameter_mm=bolt_dia,
        bolt_grade=bolt_grade,
        hole_diameter_mm=hole_dia,
        number_of_bolts=int(num_bolts),
        edge_distance_mm=edge_dist,
        end_distance_mm=end_dist,
    )
    
    # Calculate shear force (from end support reaction)
    shear_force_kn = (loads['gravity_line_load_kn_m'] * span_m) / 2
    
    # Connection check
    conn_result = connection_check(
        shear_force_kn, conn, t_mm, fy_mpa
    )
    
    st.subheader("Connection Capacity Check")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Design Shear", f"{conn_result['design_shear_kn']:.2f} kN")
    with col2:
        st.metric("Governing Capacity", f"{conn_result['governing_capacity_kn']:.2f} kN")
    with col3:
        st.metric("Governer", conn_result['governing_mode'])
    
    # Capacity breakdown
    st.write("**Capacity Components:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"Bolt Shear: {conn_result['bolt_shear_capacity_kn']:.2f} kN")
    with col2:
        st.write(f"Bearing: {conn_result['bearing_capacity_kn']:.2f} kN")
    
    # Safety status
    if conn_result['is_safe']:
        st.success(f"✅ CONNECTION SAFE - Utilization: {conn_result['utilization_ratio']:.1%}, Margin: {conn_result['margin_percent']:.1f}%")
    else:
        st.error(f"❌ CONNECTION INADEQUATE - Utilization: {conn_result['utilization_ratio']:.1%}")

# ========================================================================
# SUMMARY REPORT
# ========================================================================
st.divider()
st.header("📊 Design Summary Report")

summary_data = {
    'Check': [
        'Effective-Width',
        'LTB Analysis',
        'Biaxial Interaction',
        'Deflection (LL)',
        'Connection'
    ],
    'Status': [
        '✅ PASS' if eff_props['combined_reduction_factor'] > 0.7 else '⚠️ WARN',
        '✅ PASS' if ltb_result['is_safe'] else '❌ FAIL',
        '✅ PASS' if interaction['is_safe'] else '❌ FAIL',
        '✅ PASS' if deflection_check(loads['live_line_load_kn_m'], span_m, section_props['ixx_cm4'], 'live')['is_safe'] else '⚠️ WARN',
        '✅ PASS' if conn_result['is_safe'] else '❌ FAIL'
    ],
    'Utilization': [
        f"{(1 - eff_props['combined_reduction_factor'])*100:.1f}% reduction",
        f"{ltb_result['utilization_ratio']:.1%}",
        f"{interaction['interaction_ratio']:.1%}",
        f"{deflection_check(loads['live_line_load_kn_m'], span_m, section_props['ixx_cm4'], 'live')['utilization_ratio']:.1%}",
        f"{conn_result['utilization_ratio']:.1%}"
    ]
}

summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, use_container_width=True)

st.info("""
    ### 🎯 Design Recommendations
    
    **For Production Design:**
    1. Verify effective-width factors with detailed stress analysis
    2. Confirm LTB with actual bracing details (purlins, restraints)
    3. Check deflection against project-specific criteria
    4. Size connections for support reactions
    5. Perform detailed analysis of local buckling at concentrated loads
    6. Verify torsional stresses and warping
    
    **Code References:**
    - IS 801:1975 (Indian Standard for Cold-Formed Steel)
    - IS 875 (Code of Practice for Design Loads)
    - IS 1367 (Specifications for Fasteners)
    - IS 800 (Code of Practice for General Construction in Steel)
""")
