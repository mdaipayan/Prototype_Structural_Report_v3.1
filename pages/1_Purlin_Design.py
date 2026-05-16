import pandas as pd
import streamlit as st
from design_calcs import (
    ZPurlinASDInputs,
    z_purlin_design_analysis,
    z_purlin_design_moments,
    z_purlin_flat_width_checks,
    z_purlin_resolved_loads,
)

st.set_page_config(page_title="Z-Purlin Design IS 801:1975", layout="wide")

st.title("Cold-Formed Z-Purlin Design (IS 801:1975)")
st.markdown(
    "Complete the input form first, then run the purlin analysis and design checks. "
    "All checks, design provisions and IS code references are shown below on this same page."
)

with st.form("z_purlin_design_form"):
    st.subheader("Input Form")
    material_col, section_col, load_col, design_col = st.columns(4)

    with material_col:
        st.markdown("**1. Material & Framing**")
        fy = st.number_input(
            "Yield Strength, Fy (MPa)", min_value=1.0, value=250.0, step=10.0
        )
        span = st.number_input("Purlin Span, L (m)", min_value=0.1, value=5.0, step=0.1)
        spacing = st.number_input(
            "Purlin Spacing (m)", min_value=0.1, value=1.2, step=0.1
        )
        slope_deg = st.number_input("Roof Slope (degrees)", value=10.0, step=1.0)

    with section_col:
        st.markdown("**2. Trial Section**")
        h = st.number_input(
            "Total Depth, h (mm)", min_value=10.0, value=200.0, step=5.0
        )
        b = st.number_input("Flange Width, b (mm)", min_value=5.0, value=60.0, step=1.0)
        d_lip = st.number_input(
            "Lip Depth, d (mm)", min_value=0.0, value=20.0, step=1.0
        )
        t = st.number_input("Thickness, t (mm)", min_value=0.1, value=2.0, step=0.1)

    with load_col:
        st.markdown("**3. Service Loads (IS 875)**")
        dl = st.number_input("Dead Load (kN/m²)", value=0.15, step=0.01)
        ll = st.number_input("Live / Imposed Load (kN/m²)", value=0.75, step=0.05)
        wl = st.number_input("Wind Load - Uplift (kN/m²)", value=-1.50, step=0.1)

    with design_col:
        st.markdown("**4. Design Provisions**")
        normal_denominator = st.number_input(
            "Normal moment denominator", min_value=1.0, value=10.0, step=0.5
        )
        tangential_denominator = st.number_input(
            "Tangential moment denominator", min_value=1.0, value=8.0, step=0.5
        )
        effective_factor = st.number_input(
            "Effective section modulus factor",
            min_value=0.01,
            max_value=1.0,
            value=1.0,
            step=0.05,
        )
        ltb_factor = st.number_input(
            "LTB / restraint reduction factor",
            min_value=0.01,
            max_value=1.0,
            value=1.0,
            step=0.05,
        )

    submitted = st.form_submit_button("Run purlin design", type="primary")

if not submitted:
    st.info(
        "Enter the purlin data in the form and click **Run purlin design**. "
        "The page will then show the design summary, analysis tables and code references below."
    )
    st.stop()

validation_errors = []
if h <= 2.0 * t:
    validation_errors.append(
        "Total depth h must be greater than 2t to leave a positive clear web depth."
    )
if b <= 2.0 * t:
    validation_errors.append(
        "Flange width b must be greater than 2t to leave a positive flat flange width."
    )
if d_lip and d_lip <= t:
    validation_errors.append(
        "Lip depth d should be greater than t for a lipped Z-profile trial section."
    )

if validation_errors:
    for error in validation_errors:
        st.error(error)
    st.stop()

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
    normal_moment_denominator=normal_denominator,
    tangential_moment_denominator=tangential_denominator,
    effective_section_factor=effective_factor,
    ltb_reduction_factor=ltb_factor,
)
checks = z_purlin_flat_width_checks(inputs)
loads = z_purlin_resolved_loads(inputs)
moments = z_purlin_design_moments(inputs, loads)
design = z_purlin_design_analysis(inputs, moments)

st.success("Purlin analysis and preliminary design completed for the submitted inputs.")

st.header("Design Summary")
summary_df = pd.DataFrame(
    [
        {
            "Check": "Web flat-width ratio",
            "Code reference": "IS 801:1975 Clause 5.2",
            "Demand": f"{checks['web_ratio']:.2f}",
            "Limit": f"≤ {checks['web_ratio_limit']:.0f}",
            "Status": "OK" if checks["web_ratio_ok"] else "NOT OK",
        },
        {
            "Check": "Flange flat-width ratio with simple lip",
            "Code reference": "IS 801:1975 Clause 5.2",
            "Demand": f"{checks['flange_ratio']:.2f}",
            "Limit": f"≤ {checks['flange_ratio_limit']:.0f}",
            "Status": "OK" if checks["flange_ratio_ok"] else "NOT OK",
        },
        {
            "Check": "Gravity biaxial bending interaction",
            "Code reference": "IS 801:1975 Clause 6.7",
            "Demand": f"{design['gravity_interaction_ratio']:.3f}",
            "Limit": "≤ 1.000",
            "Status": "OK" if design["gravity_interaction_ok"] else "NOT OK",
        },
        {
            "Check": "Uplift major-axis bending interaction",
            "Code reference": "IS 801:1975 Clauses 6.3 and 6.7",
            "Demand": f"{design['uplift_interaction_ratio']:.3f}",
            "Limit": "≤ 1.000",
            "Status": "OK" if design["uplift_interaction_ok"] else "NOT OK",
        },
    ]
)
st.dataframe(summary_df, width="stretch", hide_index=True)

all_ok = (
    checks["web_ratio_ok"]
    and checks["flange_ratio_ok"]
    and design["gravity_interaction_ok"]
    and design["uplift_interaction_ok"]
)
if all_ok:
    st.success(
        "Preliminary result: trial purlin is acceptable for the submitted assumptions."
    )
else:
    st.error(
        "Preliminary result: revise the purlin size, thickness, restraint assumptions or effective-section factors."
    )

st.header("Load Resolution and Design Moments")
load_col, moment_col = st.columns(2)
with load_col:
    st.subheader("Load Resolution")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Load case": "Gravity (DL + LL)",
                    "IS loading reference": "IS 875 Part 1 + Part 2",
                    "Normal Wn (kN/m)": loads["gravity_normal_kn_m"],
                    "Tangential Wt (kN/m)": loads["gravity_tangential_kn_m"],
                },
                {
                    "Load case": "Uplift (DL + WL)",
                    "IS loading reference": "IS 875 Part 1 + Part 3",
                    "Normal Wn (kN/m)": loads["uplift_normal_kn_m"],
                    "Tangential Wt (kN/m)": loads["uplift_tangential_kn_m"],
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )
with moment_col:
    st.subheader("Design Moments")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Moment": "Gravity Mx",
                    "Formula": f"Wn L² / {moments['normal_moment_denominator']:.2f}",
                    "Value (kN-m)": moments["gravity_major_axis_kn_m"],
                },
                {
                    "Moment": "Gravity My",
                    "Formula": f"Wt L² / {moments['tangential_moment_denominator']:.2f}",
                    "Value (kN-m)": moments["gravity_minor_axis_kn_m"],
                },
                {
                    "Moment": "Uplift Mx",
                    "Formula": f"Wn L² / {moments['normal_moment_denominator']:.2f}",
                    "Value (kN-m)": moments["uplift_major_axis_kn_m"],
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

st.header("Section Properties and Design Provisions")
st.caption(
    "Gross section properties are reduced by the submitted effective-section factor. "
    "Use project-approved effective widths before issuing calculations."
)
property_df = pd.DataFrame(
    [
        {"Property": "Area", "Value": design["area_cm2"], "Unit": "cm²"},
        {"Property": "Weight", "Value": design["weight_kg_m"], "Unit": "kg/m"},
        {"Property": "Ixx", "Value": design["ixx_cm4"], "Unit": "cm⁴"},
        {"Property": "Iyy", "Value": design["iyy_cm4"], "Unit": "cm⁴"},
        {
            "Property": "Effective Zxx",
            "Value": design["zxx_effective_cm3"],
            "Unit": "cm³",
        },
        {
            "Property": "Effective Zyy",
            "Value": design["zyy_effective_cm3"],
            "Unit": "cm³",
        },
    ]
)
st.dataframe(property_df, width="stretch", hide_index=True)

stress_df = pd.DataFrame(
    [
        {
            "Case": "Gravity major-axis bending",
            "Code reference": "IS 801:1975 Clause 6.3",
            "Actual stress (N/mm²)": design["gravity_major_stress_n_mm2"],
            "Allowable stress (N/mm²)": design["allowable_stress_n_mm2"],
        },
        {
            "Case": "Gravity minor-axis bending",
            "Code reference": "IS 801:1975 Clause 6.7",
            "Actual stress (N/mm²)": design["gravity_minor_stress_n_mm2"],
            "Allowable stress (N/mm²)": design["allowable_stress_n_mm2"],
        },
        {
            "Case": "Uplift major-axis bending",
            "Code reference": "IS 801:1975 Clause 6.3",
            "Actual stress (N/mm²)": design["uplift_major_stress_n_mm2"],
            "Allowable stress (N/mm²)": design["allowable_stress_n_mm2"],
        },
    ]
)
st.dataframe(stress_df, width="stretch", hide_index=True)

st.subheader("Effective Width Framework")
st.write(
    "Use IS 801:1975 Clause 5.2.1 effective-width equations for compression elements."
)
st.latex(r"""
\frac{b}{t} = \frac{2120}{\sqrt{f}} \left[ 1 - \frac{465}{(w/t)\sqrt{f}} \right]
""")

st.header("IS Code References")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Design item": "Cold-formed element flat-width ratios",
                "Code reference": "IS 801:1975 Clause 5.2",
                "How used here": "Flags web and flange width-to-thickness ratios before stress checks.",
            },
            {
                "Design item": "Effective width of compression elements",
                "Code reference": "IS 801:1975 Clause 5.2.1",
                "How used here": "Shown as the design framework; user-entered factor reduces section modulus.",
            },
            {
                "Design item": "Bending stress / lateral restraint review",
                "Code reference": "IS 801:1975 Clause 6.3",
                "How used here": "Applies the submitted LTB/restraint factor to the ASD bending stress limit.",
            },
            {
                "Design item": "Combined biaxial bending interaction",
                "Code reference": "IS 801:1975 Clause 6.7",
                "How used here": "Checks gravity major-plus-minor bending interaction against unity.",
            },
            {
                "Design item": "Dead load input",
                "Code reference": "IS 875 Part 1",
                "How used here": "User enters project dead load intensity in kN/m².",
            },
            {
                "Design item": "Live / imposed load input",
                "Code reference": "IS 875 Part 2",
                "How used here": "User enters project imposed roof load intensity in kN/m².",
            },
            {
                "Design item": "Wind uplift input",
                "Code reference": "IS 875 Part 3",
                "How used here": "User enters project wind uplift pressure in kN/m².",
            },
        ]
    ),
    width="stretch",
    hide_index=True,
)
st.warning(
    "Clause references are provided to guide preliminary checking. Confirm the governing edition, "
    "project load combinations, coefficients, effective widths, local buckling, LTB, deflection, "
    "connections and client criteria before issuing design calculations."
)
