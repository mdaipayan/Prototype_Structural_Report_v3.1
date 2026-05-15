"""Streamlit Z-Purlin Design Page

Interactive step-by-step Z-purlin design following IS 801:1975 ASD framework
with real-time validation and PDF report generation.
"""

import streamlit as st
from datetime import datetime
from design_calcs import ZPurlinASDInputs, z_purlin_flat_width_checks, z_purlin_resolved_loads, z_purlin_design_moments
from pdf_generator import create_design_report


st.set_page_config(page_title="Z-Purlin Design", layout="wide")

st.title("🔧 Z-Purlin Design (IS 801:1975 ASD)")
st.caption("Step-by-step preliminary design screening with PDF report generation")

# Initialize session state
if "inputs" not in st.session_state:
    st.session_state.inputs = ZPurlinASDInputs()

# Step 1: Material & Roof Parameters
st.header("Step 1️⃣ Material Strength & Roof Parameters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    fy_mpa = st.number_input(
        "Yield Strength (Fy) [MPa]",
        min_value=200.0,
        max_value=450.0,
        value=st.session_state.inputs.fy_mpa,
        step=10.0,
    )

with col2:
    span_m = st.number_input(
        "Purlin Span [m]",
        min_value=1.0,
        max_value=15.0,
        value=st.session_state.inputs.span_m,
        step=0.5,
    )

with col3:
    spacing_m = st.number_input(
        "Purlin Spacing [m]",
        min_value=0.5,
        max_value=3.0,
        value=st.session_state.inputs.spacing_m,
        step=0.1,
    )

with col4:
    slope_deg = st.number_input(
        "Roof Slope [degrees]",
        min_value=0.0,
        max_value=45.0,
        value=st.session_state.inputs.slope_deg,
        step=1.0,
    )

st.session_state.inputs.fy_mpa = fy_mpa
st.session_state.inputs.span_m = span_m
st.session_state.inputs.spacing_m = spacing_m
st.session_state.inputs.slope_deg = slope_deg

# Step 2: Z-Section Dimensions
st.header("Step 2️⃣ Trial Z-Section Dimensions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_depth_h_mm = st.number_input(
        "Total Depth (h) [mm]",
        min_value=100.0,
        max_value=400.0,
        value=st.session_state.inputs.total_depth_h_mm,
        step=10.0,
    )

with col2:
    flange_width_b_mm = st.number_input(
        "Flange Width (b) [mm]",
        min_value=40.0,
        max_value=120.0,
        value=st.session_state.inputs.flange_width_b_mm,
        step=5.0,
    )

with col3:
    lip_depth_d_mm = st.number_input(
        "Lip Depth (d) [mm]",
        min_value=10.0,
        max_value=40.0,
        value=st.session_state.inputs.lip_depth_d_mm,
        step=2.0,
    )

with col4:
    thickness_t_mm = st.number_input(
        "Thickness (t) [mm]",
        min_value=1.2,
        max_value=4.0,
        value=st.session_state.inputs.thickness_t_mm,
        step=0.2,
    )

st.session_state.inputs.total_depth_h_mm = total_depth_h_mm
st.session_state.inputs.flange_width_b_mm = flange_width_b_mm
st.session_state.inputs.lip_depth_d_mm = lip_depth_d_mm
st.session_state.inputs.thickness_t_mm = thickness_t_mm

# Step 3: Service Loads
st.header("Step 3️⃣ Service Loads [kN/m²]")
col1, col2, col3 = st.columns(3)

with col1:
    dead_load_kn_m2 = st.number_input(
        "Dead Load (DL) [kN/m²]",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.inputs.dead_load_kn_m2,
        step=0.05,
        format="%.3f",
    )

with col2:
    live_load_kn_m2 = st.number_input(
        "Live Load (LL) [kN/m²]",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.inputs.live_load_kn_m2,
        step=0.05,
        format="%.3f",
    )

with col3:
    wind_load_kn_m2 = st.number_input(
        "Wind Load (WL) [kN/m²] (negative for uplift)",
        min_value=-3.0,
        max_value=0.0,
        value=st.session_state.inputs.wind_load_kn_m2,
        step=0.05,
        format="%.3f",
    )

st.session_state.inputs.dead_load_kn_m2 = dead_load_kn_m2
st.session_state.inputs.live_load_kn_m2 = live_load_kn_m2
st.session_state.inputs.wind_load_kn_m2 = wind_load_kn_m2

# Step 4: Preliminary Checks
st.header("Step 4️⃣ Preliminary Checks (IS 801:1975 Clause 5.2)")

checks = z_purlin_flat_width_checks(st.session_state.inputs)

col1, col2 = st.columns(2)

with col1:
    status = "✅ PASS" if checks["web_ratio_ok"] else "❌ FAIL"
    st.metric(
        "Web h/t Ratio",
        f"{checks['web_ratio']:.1f}",
        f"Limit: {checks['web_ratio_limit']:.0f}",
    )
    st.write(status)

with col2:
    status = "✅ PASS" if checks["flange_ratio_ok"] else "❌ FAIL"
    st.metric(
        "Flange b/t Ratio",
        f"{checks['flange_ratio']:.1f}",
        f"Limit: {checks['flange_ratio_limit']:.0f}",
    )
    st.write(status)

# Step 5: Resolved Line Loads
st.header("Step 5️⃣ Resolved Line Loads on Sloped Roof")

resolved_loads = z_purlin_resolved_loads(st.session_state.inputs)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Gravity Loads (DL+LL)")
    st.metric(
        "Total Line Load",
        f"{resolved_loads['gravity_line_load_kn_m']:.4f}",
        "kN/m"
    )
    st.metric(
        "Normal Component",
        f"{resolved_loads['gravity_normal_kn_m']:.4f}",
        "kN/m"
    )
    st.metric(
        "Tangential Component",
        f"{resolved_loads['gravity_tangential_kn_m']:.4f}",
        "kN/m"
    )

with col2:
    st.subheader("Uplift Loads (DL+WL)")
    st.metric(
        "Total Line Load",
        f"{resolved_loads['uplift_line_load_kn_m']:.4f}",
        "kN/m"
    )
    st.metric(
        "Normal Component",
        f"{resolved_loads['uplift_normal_kn_m']:.4f}",
        "kN/m"
    )
    st.metric(
        "Tangential Component",
        f"{resolved_loads['uplift_tangential_kn_m']:.4f}",
        "kN/m"
    )

# Step 6: Design Moments
st.header("Step 6️⃣ Design Moments (Continuous Span)")

design_moments = z_purlin_design_moments(st.session_state.inputs, resolved_loads)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Gravity Cases")
    st.metric(
        "Major Axis (Normal)",
        f"{design_moments['gravity_major_axis_kn_m']:.4f}",
        "kN-m"
    )
    st.metric(
        "Minor Axis (Tangential)",
        f"{design_moments['gravity_minor_axis_kn_m']:.4f}",
        "kN-m"
    )

with col2:
    st.subheader("Uplift Case")
    st.metric(
        "Major Axis (Normal)",
        f"{design_moments['uplift_major_axis_kn_m']:.4f}",
        "kN-m"
    )

with col3:
    st.subheader("Design Formula")
    st.write("**Normal:** WL²/10")
    st.write("**Tangential:** WL²/8")
    st.write("*(Continuous span)*")

# Step 7: PDF Report Generation
st.header("Step 7️⃣ Generate PDF Report")

col1, col2, col3 = st.columns(3)

with col1:
    project_name = st.text_input("Project Name", value="Z-Purlin Design Project")

with col2:
    location = st.text_input("Project Location", value="India")

with col3:
    designer = st.text_input("Designer Name", value="Structural Engineer")

if st.button("📥 Download PDF Report", use_container_width=True, type="primary"):
    try:
        # Prepare inputs dictionary
        inputs_dict = {
            'fy_mpa': st.session_state.inputs.fy_mpa,
            'span_m': st.session_state.inputs.span_m,
            'spacing_m': st.session_state.inputs.spacing_m,
            'slope_deg': st.session_state.inputs.slope_deg,
            'total_depth_h_mm': st.session_state.inputs.total_depth_h_mm,
            'flange_width_b_mm': st.session_state.inputs.flange_width_b_mm,
            'lip_depth_d_mm': st.session_state.inputs.lip_depth_d_mm,
            'thickness_t_mm': st.session_state.inputs.thickness_t_mm,
            'dead_load_kn_m2': st.session_state.inputs.dead_load_kn_m2,
            'live_load_kn_m2': st.session_state.inputs.live_load_kn_m2,
            'wind_load_kn_m2': st.session_state.inputs.wind_load_kn_m2,
        }
        
        # Generate PDF
        pdf_bytes = create_design_report(
            inputs=inputs_dict,
            flat_width_checks=checks,
            resolved_loads=resolved_loads,
            design_moments=design_moments,
            project_name=project_name,
            location=location,
            designer=designer,
        )
        
        # Create download button
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Z_Purlin_Design_{timestamp}.pdf"
        
        st.download_button(
            label="✅ Click to Download PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )
        st.success(f"✅ PDF generated successfully as: {filename}")
        
    except Exception as e:
        st.error(f"❌ Error generating PDF: {str(e)}")

# Design Notes
st.divider()
st.info("""
    ### 📋 Design Notes & Limitations
    
    **Included in this screening:**
    - Flat-width ratio checks per IS 801:1975 Clause 5.2
    - Load resolution on sloped roofs
    - Preliminary moment calculations (continuous span)
    
    **NOT included (requires manual verification):**
    - Effective-width reduction analysis
    - Lateral-torsional buckling (LTB)
    - Biaxial bending interaction
    - Deflection checks
    - Connection design
    
    **Always verify with:**
    - Project-specific code requirements
    - Manufacturer section properties
    - Final stress and buckling checks before issuing calculations
""")
