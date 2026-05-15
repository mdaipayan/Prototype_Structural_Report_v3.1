import pandas as pd
import streamlit as st
from design_calcs import (
    ZPurlinASDInputs,
    z_purlin_design_moments,
    z_purlin_flat_width_checks,
    z_purlin_resolved_loads,
)

st.set_page_config(page_title="Z-Purlin Design IS 801:1975", layout="wide")

st.title("Cold-Formed Z-Purlin Design (IS 801:1975)")
st.markdown(
    "Automated preliminary design checks and load resolution based on the "
    "Allowable Stress Design (ASD) methodology."
)

st.sidebar.header("1. Material & Geometry")
fy = st.sidebar.number_input("Yield Strength, Fy (MPa)", value=250.0, step=10.0)
span = st.sidebar.number_input("Purlin Span, L (m)", value=5.0, step=0.1)
spacing = st.sidebar.number_input("Purlin Spacing (m)", value=1.2, step=0.1)
slope_deg = st.sidebar.number_input("Roof Slope (degrees)", value=10.0, step=1.0)

st.sidebar.subheader("Trial Section (Z-Profile with Lips)")
h = st.sidebar.number_input("Total Depth, h (mm)", value=200.0, step=5.0)
b = st.sidebar.number_input("Flange Width, b (mm)", value=60.0, step=1.0)
d_lip = st.sidebar.number_input("Lip Depth, d (mm)", value=20.0, step=1.0)
t = st.sidebar.number_input("Thickness, t (mm)", value=2.0, step=0.1)

st.sidebar.header("2. Loading (IS 875)")
dl = st.sidebar.number_input("Dead Load (kN/m²)", value=0.15, step=0.01)
ll = st.sidebar.number_input("Live Load (kN/m²)", value=0.75, step=0.05)
wl = st.sidebar.number_input("Wind Load - Uplift (kN/m²)", value=-1.50, step=0.1)

inputs = ZPurlinASDInputs(
    fy_mpa=fy,
    span_m=span,
    spacing_m=spacing,
    slope_deg=slope_deg,
    total_depth_h_mm=h,
    flange_width_b_mm=b,
    lip_depth_d_mm=d_lip,
    thickness_t_mm=t,
    dead_load_kn_m2=dl,
    live_load_kn_m2=ll,
    wind_load_kn_m2=wl,
)
checks = z_purlin_flat_width_checks(inputs)
loads = z_purlin_resolved_loads(inputs)
moments = z_purlin_design_moments(inputs, loads)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Step 1: Geometric Limits Check (Clause 5.2)")
    st.caption(
        "Flat-width calculations are simplified for preliminary review and ignore corner radii."
    )

    st.write(f"**Web Flat-Width Ratio ($h/t$):** {checks['web_ratio']:.2f}")
    if checks["web_ratio_ok"]:
        st.success("Web ratio is within the preliminary limit (≤ 150).")
    else:
        st.error("Web ratio exceeds limit. Add stiffeners or increase thickness.")

    st.write(f"**Flange Flat-Width Ratio ($w/t$):** {checks['flange_ratio']:.2f}")
    if checks["flange_ratio_ok"]:
        st.success("Flange ratio is within the limit for simple lips (≤ 60).")
    else:
        st.error("Flange ratio exceeds the limit for simple lip edge stiffeners (60).")

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Element": "Web",
                    "Flat width (mm)": checks["web_flat_width_mm"],
                    "Ratio": checks["web_ratio"],
                    "Limit": checks["web_ratio_limit"],
                    "Status": "OK" if checks["web_ratio_ok"] else "NOT OK",
                },
                {
                    "Element": "Flange",
                    "Flat width (mm)": checks["flange_flat_width_mm"],
                    "Ratio": checks["flange_ratio"],
                    "Limit": checks["flange_ratio_limit"],
                    "Status": "OK" if checks["flange_ratio_ok"] else "NOT OK",
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

with col2:
    st.subheader("Step 2: Load Resolution")

    st.markdown("**Gravity Loads (DL + LL):**")
    st.write(f"Normal Component ($W_n$): {loads['gravity_normal_kn_m']:.2f} kN/m")
    st.write(
        f"Tangential Component ($W_t$): {loads['gravity_tangential_kn_m']:.2f} kN/m"
    )

    st.markdown("**Uplift Loads (DL + WL):**")
    st.write(f"Normal Component ($W_n$): {loads['uplift_normal_kn_m']:.2f} kN/m")
    st.write(
        f"Tangential Component ($W_t$): {loads['uplift_tangential_kn_m']:.2f} kN/m"
    )

    st.dataframe(
        pd.DataFrame([loads]).T.rename(columns={0: "Value"}),
        width="stretch",
    )

st.divider()

st.subheader("Step 3: Maximum Bending Moments")
st.markdown(
    "Assuming the purlin is continuous over supports, moments are approximated as "
    "$WL^2/10$ for normal loading and $WL^2/8$ for tangential loading."
)

col3, col4 = st.columns(2)

with col3:
    st.markdown("**Gravity Combination (Top Flange in Compression)**")
    st.info(
        f"Major Axis Moment ($M_x$): **{moments['gravity_major_axis_kn_m']:.2f} kN-m**"
    )
    st.info(
        f"Minor Axis Moment ($M_y$): **{moments['gravity_minor_axis_kn_m']:.2f} kN-m**"
    )

with col4:
    st.markdown("**Uplift Combination (Bottom Flange in Compression)**")
    st.info(
        f"Major Axis Moment ($M_x$): **{moments['uplift_major_axis_kn_m']:.2f} kN-m**"
    )
    st.write(
        "*Note: wind load acts normally to the roof surface. Tangential load is "
        "usually resisted by sag rods.*"
    )

st.divider()

st.subheader("Step 4: Effective Properties & Stress Checks (Framework)")
st.write(
    "To complete the application, integrate the effective-width equations from "
    "IS 801 Clause 5.2.1:"
)

st.latex(r"""
\frac{b}{t} = \frac{2120}{\sqrt{f}} \left[ 1 - \frac{465}{(w/t)\sqrt{f}} \right]
""")

st.code(
    """
# Algorithmic flow for iterative stress checks:
# 1. Assume f = 0.60 * Fy
# 2. Calculate effective width (b) of the compression flange.
# 3. Calculate effective Ixx, Iyy, Zxx, Zyy.
# 4. Calculate actual stress: f_actual = M / Z_eff
# 5. If f_actual exceeds assumed f, iterate until convergence.
# 6. Apply Lateral Torsional Buckling checks (Clause 6.3) and biaxial bending interaction (Clause 6.7).
""",
    language="python",
)

st.warning(
    "This tool is for preliminary ASD screening only. Verify final member design, "
    "effective widths, LTB, interaction checks, connections and project criteria "
    "before issuing calculations."
)
