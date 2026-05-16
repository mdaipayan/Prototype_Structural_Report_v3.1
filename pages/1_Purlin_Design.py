"""Complete Streamlit Z-purlin design page.

All current cold-formed design workflows live on this single page so users do
not need to jump between preliminary and advanced analysis pages.
"""

from dataclasses import asdict

import pandas as pd
import streamlit as st

from advanced_checks import (
    BoltConnection,
    biaxial_interaction_check,
    connection_check,
    deflection_check,
    effective_section_properties,
    ltb_check,
)
from design_calcs import (
    ZPurlinASDInputs,
    z_purlin_design_analysis,
    z_purlin_design_moments,
    z_purlin_flat_width_checks,
    z_purlin_resolved_loads,
)
from pdf_generator import create_design_report

COMMON_Z_PURLIN_CATALOG = {
    "depths_mm": [150.0, 175.0, 200.0, 225.0, 250.0, 275.0, 300.0, 350.0],
    "flanges_mm": [50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
    "lips_mm": [15.0, 20.0, 25.0],
    "thicknesses_mm": [1.5, 2.0, 2.5, 3.0],
}


def section_name(section: dict[str, float]) -> str:
    """Return a compact Z-section label."""
    return (
        f"Z {section['total_depth_h_mm']:.0f} × {section['flange_width_b_mm']:.0f} × "
        f"{section['lip_depth_d_mm']:.0f} × {section['thickness_t_mm']:.2f} mm"
    )


def find_optimal_section(
    base_inputs: ZPurlinASDInputs,
    unbraced_length_m: float,
    ltb_support_condition: str,
    deflection_support_condition: str,
    connection: BoltConnection,
) -> dict:
    """Find the lightest catalog Z-purlin that passes the included checks.

    If no catalog section passes, return the lowest-utilization candidate so the
    designer still gets a clear direction for increasing section size.
    """
    candidate_dimensions = set()
    for depth in COMMON_Z_PURLIN_CATALOG["depths_mm"] + [base_inputs.total_depth_h_mm]:
        for flange in COMMON_Z_PURLIN_CATALOG["flanges_mm"] + [
            base_inputs.flange_width_b_mm
        ]:
            for lip in COMMON_Z_PURLIN_CATALOG["lips_mm"] + [
                base_inputs.lip_depth_d_mm
            ]:
                for thickness in COMMON_Z_PURLIN_CATALOG["thicknesses_mm"] + [
                    base_inputs.thickness_t_mm
                ]:
                    if (
                        depth <= 2.0 * thickness
                        or flange <= 2.0 * thickness
                        or lip <= thickness
                    ):
                        continue
                    candidate_dimensions.add((depth, flange, lip, thickness))

    evaluated_candidates = []
    for depth, flange, lip, thickness in sorted(candidate_dimensions):
        candidate_inputs = ZPurlinASDInputs(
            fy_mpa=base_inputs.fy_mpa,
            span_m=base_inputs.span_m,
            spacing_m=base_inputs.spacing_m,
            slope_deg=base_inputs.slope_deg,
            total_depth_h_mm=depth,
            flange_width_b_mm=flange,
            lip_depth_d_mm=lip,
            thickness_t_mm=thickness,
            dead_load_kn_m2=base_inputs.dead_load_kn_m2,
            live_load_kn_m2=base_inputs.live_load_kn_m2,
            wind_load_kn_m2=base_inputs.wind_load_kn_m2,
            normal_moment_denominator=base_inputs.normal_moment_denominator,
            tangential_moment_denominator=base_inputs.tangential_moment_denominator,
            effective_section_factor=base_inputs.effective_section_factor,
            ltb_reduction_factor=base_inputs.ltb_reduction_factor,
        )
        candidate_checks = z_purlin_flat_width_checks(candidate_inputs)
        candidate_loads = z_purlin_resolved_loads(candidate_inputs)
        candidate_moments = z_purlin_design_moments(candidate_inputs, candidate_loads)
        candidate_design = z_purlin_design_analysis(candidate_inputs, candidate_moments)
        candidate_max_stress = max(
            candidate_design["gravity_major_stress_n_mm2"],
            candidate_design["uplift_major_stress_n_mm2"],
        )
        candidate_effective = effective_section_properties(
            candidate_design,
            candidate_checks,
            candidate_inputs.fy_mpa,
            candidate_max_stress,
        )
        candidate_ltb = ltb_check(
            candidate_max_stress,
            unbraced_length_m,
            candidate_design,
            ltb_support_condition,
            candidate_inputs.fy_mpa,
        )
        candidate_interaction = biaxial_interaction_check(
            candidate_design["gravity_major_stress_n_mm2"],
            candidate_design["gravity_minor_stress_n_mm2"],
            candidate_ltb["allowable_stress_mpa"],
            candidate_design["allowable_stress_n_mm2"],
        )
        candidate_live_deflection = deflection_check(
            candidate_loads["live_line_load_kn_m"],
            candidate_inputs.span_m,
            candidate_effective["effective_ixx_cm4"],
            load_type="live",
            support_condition=deflection_support_condition,
        )
        candidate_wind_deflection = deflection_check(
            abs(candidate_loads["wind_line_load_kn_m"]),
            candidate_inputs.span_m,
            candidate_effective["effective_ixx_cm4"],
            load_type="wind",
            support_condition=deflection_support_condition,
        )
        candidate_shear = max(
            abs(
                candidate_loads["gravity_line_load_kn_m"]
                * candidate_inputs.span_m
                / 2.0
            ),
            abs(
                candidate_loads["uplift_line_load_kn_m"] * candidate_inputs.span_m / 2.0
            ),
        )
        candidate_connection = connection_check(
            candidate_shear,
            connection,
            candidate_inputs.thickness_t_mm,
            candidate_inputs.fy_mpa,
        )
        governing_utilization = max(
            candidate_checks["web_ratio"] / candidate_checks["web_ratio_limit"],
            candidate_checks["flange_ratio"] / candidate_checks["flange_ratio_limit"],
            candidate_design["gravity_interaction_ratio"],
            candidate_design["uplift_interaction_ratio"],
            candidate_ltb["utilization_ratio"],
            candidate_interaction["interaction_ratio"],
            candidate_live_deflection["utilization_ratio"],
            candidate_wind_deflection["utilization_ratio"],
            candidate_connection["utilization_ratio"],
        )
        passes = all(
            [
                candidate_checks["web_ratio_ok"],
                candidate_checks["flange_ratio_ok"],
                candidate_design["gravity_interaction_ok"],
                candidate_design["uplift_interaction_ok"],
                candidate_ltb["is_safe"],
                candidate_interaction["is_safe"],
                candidate_live_deflection["is_safe"],
                candidate_wind_deflection["is_safe"],
                candidate_connection["is_safe"],
            ]
        )
        evaluated_candidates.append(
            {
                "section": asdict(candidate_inputs),
                "name": section_name(asdict(candidate_inputs)),
                "weight_kg_m": candidate_design["weight_kg_m"],
                "governing_utilization": governing_utilization,
                "passes": passes,
                "design": candidate_design,
                "checks": candidate_checks,
                "ltb": candidate_ltb,
                "interaction": candidate_interaction,
                "live_deflection": candidate_live_deflection,
                "wind_deflection": candidate_wind_deflection,
                "connection": candidate_connection,
            }
        )

    passing_candidates = [
        candidate for candidate in evaluated_candidates if candidate["passes"]
    ]
    if passing_candidates:
        return min(
            passing_candidates,
            key=lambda candidate: (
                candidate["weight_kg_m"],
                candidate["governing_utilization"],
                candidate["section"]["total_depth_h_mm"],
            ),
        )

    return min(
        evaluated_candidates,
        key=lambda candidate: (
            candidate["governing_utilization"],
            candidate["weight_kg_m"],
            -candidate["section"]["total_depth_h_mm"],
        ),
    )


def status_label(
    is_ok: bool, pass_label: str = "PASS", fail_label: str = "REVIEW"
) -> str:
    """Return a user-friendly status label for summary tables."""
    return f"✅ {pass_label}" if is_ok else f"⚠️ {fail_label}"


def show_status_message(is_ok: bool, success_text: str, warning_text: str) -> None:
    """Show a consistent status callout."""
    if is_ok:
        st.success(success_text)
    else:
        st.warning(warning_text)


st.set_page_config(page_title="Complete Z-Purlin Design", layout="wide")

st.title("Complete Cold-Formed Z-Purlin Design")
st.caption(
    "Step-by-step preliminary design with IS 801:1975, IS 875 and connection-reference notes."
)

st.info(
    "Use this page as a guided calculation scaffold. Enter project-specific values, run the design, "
    "then review each numbered step from geometry through final references."
)

with st.form("z_purlin_design_form"):
    st.subheader("1) Enter design inputs")
    st.write(
        "Default values are provided so you can run a quick sample design immediately."
    )

    material_col, section_col, load_col = st.columns(3)

    with material_col:
        st.markdown("**Material and framing**")
        fy = st.number_input(
            "Yield strength, Fy (MPa)", min_value=1.0, value=250.0, step=10.0
        )
        span = st.number_input("Purlin span, L (m)", min_value=0.1, value=5.0, step=0.1)
        spacing = st.number_input(
            "Purlin spacing (m)", min_value=0.1, value=1.2, step=0.1
        )
        slope_deg = st.number_input("Roof slope (degrees)", value=10.0, step=1.0)

    with section_col:
        st.markdown("**Trial Z-section**")
        h = st.number_input(
            "Total depth, h (mm)", min_value=10.0, value=200.0, step=5.0
        )
        b = st.number_input("Flange width, b (mm)", min_value=5.0, value=60.0, step=1.0)
        d_lip = st.number_input(
            "Lip depth, d (mm)", min_value=0.0, value=20.0, step=1.0
        )
        t = st.number_input("Thickness, t (mm)", min_value=0.1, value=2.0, step=0.1)

    with load_col:
        st.markdown("**Service loads (IS 875 inputs)**")
        dl = st.number_input("Dead load, DL (kN/m²)", value=0.15, step=0.01)
        ll = st.number_input("Live / imposed load, LL (kN/m²)", value=0.75, step=0.05)
        wl = st.number_input(
            "Wind load, WL uplift negative (kN/m²)", value=-1.50, step=0.1
        )

    with st.expander("Advanced design assumptions", expanded=True):
        design_col, service_col, connection_col = st.columns(3)

        with design_col:
            st.markdown("**Strength assumptions**")
            normal_denominator = st.number_input(
                "Normal moment denominator", min_value=1.0, value=10.0, step=0.5
            )
            tangential_denominator = st.number_input(
                "Tangential moment denominator", min_value=1.0, value=8.0, step=0.5
            )
            effective_factor = st.number_input(
                "User effective section modulus factor",
                min_value=0.01,
                max_value=1.0,
                value=1.0,
                step=0.05,
                help="Additional project-specific effective-section factor applied in the base ASD check.",
            )
            ltb_factor = st.number_input(
                "User LTB / restraint reduction factor",
                min_value=0.01,
                max_value=1.0,
                value=1.0,
                step=0.05,
                help="Additional project-specific reduction factor applied in the base ASD check.",
            )

        with service_col:
            st.markdown("**LTB and deflection**")
            unbraced_length = st.number_input(
                "Unbraced length for LTB (m)", min_value=0.1, value=span, step=0.1
            )
            ltb_support = st.selectbox(
                "LTB support condition",
                [
                    "continuous",
                    "simply_supported",
                    "fixed_one_end",
                    "fixed_both_ends",
                    "cantilever",
                ],
            )
            deflection_support = st.selectbox(
                "Deflection support condition",
                ["continuous_span", "simply_supported", "fixed_both_ends"],
            )

        with connection_col:
            st.markdown("**Support connection**")
            bolt_dia = st.number_input("Bolt diameter (mm)", 12.0, 24.0, 16.0, step=2.0)
            bolt_grade = st.selectbox(
                "Bolt grade",
                ["4.6", "4.8", "5.6", "5.8", "6.8", "8.8", "10.9"],
                index=5,
            )
            num_bolts = st.number_input("Number of bolts", 1, 8, 2)
            hole_dia = st.number_input("Hole diameter (mm)", 12.0, 30.0, 18.0, step=1.0)
            edge_dist = st.number_input(
                "Edge distance (mm)", 20.0, 80.0, 30.0, step=5.0
            )
            end_dist = st.number_input("End distance (mm)", 20.0, 100.0, 40.0, step=5.0)

    submitted = st.form_submit_button("Run complete Z-purlin design", type="primary")

if not submitted:
    st.info(
        "Enter the purlin data and click **Run complete Z-purlin design** to see the full summary, "
        "strength checks, serviceability checks, connection screening and code-reference notes."
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
if hole_dia < bolt_dia:
    validation_errors.append(
        "Hole diameter should not be smaller than the bolt diameter."
    )

if validation_errors:
    st.error("Please fix the following inputs before running the design:")
    for error in validation_errors:
        st.write(f"- {error}")
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

max_major_stress = max(
    design["gravity_major_stress_n_mm2"], design["uplift_major_stress_n_mm2"]
)
effective_props = effective_section_properties(design, checks, fy, max_major_stress)
ltb_result = ltb_check(max_major_stress, unbraced_length, design, ltb_support, fy)
interaction = biaxial_interaction_check(
    design["gravity_major_stress_n_mm2"],
    design["gravity_minor_stress_n_mm2"],
    ltb_result["allowable_stress_mpa"],
    design["allowable_stress_n_mm2"],
)
live_deflection = deflection_check(
    loads["live_line_load_kn_m"],
    span,
    effective_props["effective_ixx_cm4"],
    load_type="live",
    support_condition=deflection_support,
)
wind_deflection = deflection_check(
    abs(loads["wind_line_load_kn_m"]),
    span,
    effective_props["effective_ixx_cm4"],
    load_type="wind",
    support_condition=deflection_support,
)
connection = BoltConnection(
    bolt_diameter_mm=bolt_dia,
    bolt_grade=bolt_grade,
    hole_diameter_mm=hole_dia,
    number_of_bolts=int(num_bolts),
    edge_distance_mm=edge_dist,
    end_distance_mm=end_dist,
)
design_shear = max(
    abs(loads["gravity_line_load_kn_m"] * span / 2.0),
    abs(loads["uplift_line_load_kn_m"] * span / 2.0),
)
connection_result = connection_check(design_shear, connection, t, fy)
optimal_section = find_optimal_section(
    inputs,
    unbraced_length,
    ltb_support,
    deflection_support,
    connection,
)

all_ok = all(
    [
        checks["web_ratio_ok"],
        checks["flange_ratio_ok"],
        design["gravity_interaction_ok"],
        design["uplift_interaction_ok"],
        ltb_result["is_safe"],
        interaction["is_safe"],
        live_deflection["is_safe"],
        wind_deflection["is_safe"],
        connection_result["is_safe"],
    ]
)

st.divider()
st.subheader("2) Design result")
show_status_message(
    all_ok,
    "Overall screening result: the trial Z-purlin passes the included preliminary checks.",
    "Overall screening result: one or more items need engineering review or revised inputs.",
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Gravity interaction", f"{design['gravity_interaction_ratio']:.1%}")
metric_2.metric("Uplift interaction", f"{design['uplift_interaction_ratio']:.1%}")
metric_3.metric("LTB utilization", f"{ltb_result['utilization_ratio']:.1%}")
metric_4.metric(
    "Connection utilization", f"{connection_result['utilization_ratio']:.1%}"
)

st.subheader("Most optimal section size from built-in catalog")
if optimal_section["passes"]:
    st.success(
        "Recommended lightest passing section: "
        f"**{optimal_section['name']}** "
        f"({optimal_section['weight_kg_m']:.2f} kg/m, governing utilization "
        f"{optimal_section['governing_utilization']:.1%})."
    )
else:
    st.warning(
        "No built-in catalog section passed every included check. Closest option for engineering review: "
        f"**{optimal_section['name']}** "
        f"({optimal_section['weight_kg_m']:.2f} kg/m, governing utilization "
        f"{optimal_section['governing_utilization']:.1%})."
    )
st.dataframe(
    pd.DataFrame(
        [
            {
                "Recommended section": optimal_section["name"],
                "Weight (kg/m)": f"{optimal_section['weight_kg_m']:.2f}",
                "Governing utilization": f"{optimal_section['governing_utilization']:.1%}",
                "Catalog result": (
                    "Passes all included checks"
                    if optimal_section["passes"]
                    else "Closest option - review required"
                ),
            }
        ]
    ),
    width="stretch",
    hide_index=True,
)

pdf_bytes = create_design_report(
    asdict(inputs),
    checks,
    loads,
    moments,
    design=design,
    effective_props=effective_props,
    ltb_result=ltb_result,
    interaction=interaction,
    live_deflection=live_deflection,
    wind_deflection=wind_deflection,
    connection_result=connection_result,
    optimal_section=optimal_section,
    all_ok=all_ok,
)
st.download_button(
    "Download purlin PDF report",
    data=pdf_bytes,
    file_name="z_purlin_design_report.pdf",
    mime="application/pdf",
    type="primary",
    help="Download a step-by-step report with formulas, values, references, permissible limits, the optimal catalog section and conclusion.",
)

summary_df = pd.DataFrame(
    [
        {
            "Design step": "Step 1 - Web flat-width ratio",
            "Code reference": "IS 801:1975 Clause 5.2",
            "Demand": f"{checks['web_ratio']:.2f}",
            "Limit / capacity": f"≤ {checks['web_ratio_limit']:.0f}",
            "Status": status_label(checks["web_ratio_ok"]),
        },
        {
            "Design step": "Step 1 - Flange flat-width ratio",
            "Code reference": "IS 801:1975 Clause 5.2",
            "Demand": f"{checks['flange_ratio']:.2f}",
            "Limit / capacity": f"≤ {checks['flange_ratio_limit']:.0f}",
            "Status": status_label(checks["flange_ratio_ok"]),
        },
        {
            "Design step": "Step 4 - Gravity bending interaction",
            "Code reference": "IS 801:1975 Clauses 6.3 and 6.7",
            "Demand": f"{design['gravity_interaction_ratio']:.3f}",
            "Limit / capacity": "≤ 1.000",
            "Status": status_label(design["gravity_interaction_ok"]),
        },
        {
            "Design step": "Step 4 - Uplift bending interaction",
            "Code reference": "IS 801:1975 Clauses 6.3 and 6.7",
            "Demand": f"{design['uplift_interaction_ratio']:.3f}",
            "Limit / capacity": "≤ 1.000",
            "Status": status_label(design["uplift_interaction_ok"]),
        },
        {
            "Design step": "Step 5 - Lateral-torsional buckling",
            "Code reference": "IS 801:1975 bending restraint guidance",
            "Demand": f"{ltb_result['utilization_ratio']:.1%}",
            "Limit / capacity": "≤ 100%",
            "Status": status_label(ltb_result["is_safe"]),
        },
        {
            "Design step": "Step 5 - Biaxial bending interaction",
            "Code reference": "IS 801:1975 Clause 6.7",
            "Demand": f"{interaction['interaction_ratio']:.3f}",
            "Limit / capacity": "≤ 1.000",
            "Status": status_label(interaction["is_safe"]),
        },
        {
            "Design step": "Step 6 - Live-load deflection",
            "Code reference": "Project serviceability criteria / IS 875 load case",
            "Demand": f"{live_deflection['actual_deflection_mm']:.2f} mm",
            "Limit / capacity": f"≤ {live_deflection['limit_deflection_mm']:.2f} mm",
            "Status": status_label(live_deflection["is_safe"]),
        },
        {
            "Design step": "Step 6 - Wind-load deflection",
            "Code reference": "Project serviceability criteria / IS 875 wind load",
            "Demand": f"{wind_deflection['actual_deflection_mm']:.2f} mm",
            "Limit / capacity": f"≤ {wind_deflection['limit_deflection_mm']:.2f} mm",
            "Status": status_label(wind_deflection["is_safe"]),
        },
        {
            "Design step": "Step 7 - Support connection shear",
            "Code reference": "IS 1367 / IS 800 connection guidance",
            "Demand": f"{connection_result['design_shear_kn']:.2f} kN",
            "Limit / capacity": f"{connection_result['governing_capacity_kn']:.2f} kN",
            "Status": status_label(connection_result["is_safe"]),
        },
    ]
)
st.dataframe(summary_df, width="stretch", hide_index=True)

summary_tab, loads_tab, section_tab, advanced_tab, references_tab = st.tabs(
    [
        "Step 1 - Geometry",
        "Steps 2-3 - Loads & moments",
        "Step 4 - Section & stress",
        "Steps 5-7 - Advanced checks",
        "Step 8 - Code notes",
    ]
)

with summary_tab:
    st.subheader("Step 1: Geometry and flat-width checks")
    st.markdown("""
        - **PASS** means the trial input is within the simplified screening limit shown in this app.
        - **REVIEW** means the section, thickness, load, restraint, connection or project criteria should be revised.
        - The flat-width checks are shown first because IS 801:1975 Clause 5.2 element proportioning affects the later stress checks.
        """)
    st.dataframe(
        pd.DataFrame(
            [
                {"Input": "Fy", "Value": fy, "Unit": "MPa"},
                {"Input": "Span", "Value": span, "Unit": "m"},
                {"Input": "Spacing", "Value": spacing, "Unit": "m"},
                {"Input": "Slope", "Value": slope_deg, "Unit": "degrees"},
                {
                    "Input": "Section h × b × lip × t",
                    "Value": f"{h:.1f} × {b:.1f} × {d_lip:.1f} × {t:.1f}",
                    "Unit": "mm",
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

with loads_tab:
    st.subheader("Step 2: Resolve IS 875 service loads")
    st.caption(
        "Dead, live/imposed and wind inputs are entered as service pressures and converted to purlin line loads."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Load component": "Dead line load",
                    "Value": loads["dead_line_load_kn_m"],
                    "Unit": "kN/m",
                },
                {
                    "Load component": "Live line load",
                    "Value": loads["live_line_load_kn_m"],
                    "Unit": "kN/m",
                },
                {
                    "Load component": "Wind line load",
                    "Value": loads["wind_line_load_kn_m"],
                    "Unit": "kN/m",
                },
                {
                    "Load component": "Gravity normal component",
                    "Value": loads["gravity_normal_kn_m"],
                    "Unit": "kN/m",
                },
                {
                    "Load component": "Gravity tangential component",
                    "Value": loads["gravity_tangential_kn_m"],
                    "Unit": "kN/m",
                },
                {
                    "Load component": "Uplift normal component",
                    "Value": loads["uplift_normal_kn_m"],
                    "Unit": "kN/m",
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Step 3: Calculate preliminary design moments")
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

with section_tab:
    st.subheader("Step 4: Section properties and ASD stress checks")
    st.caption(
        "Gross properties are reduced by user-entered effective-section and restraint factors for preliminary screening."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {"Property": "Gross area", "Value": design["area_cm2"], "Unit": "cm²"},
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
        ),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Base ASD stress checks")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Case": "Gravity major-axis bending",
                    "Actual stress (MPa)": design["gravity_major_stress_n_mm2"],
                    "Allowable stress (MPa)": design["allowable_stress_n_mm2"],
                },
                {
                    "Case": "Gravity minor-axis bending",
                    "Actual stress (MPa)": design["gravity_minor_stress_n_mm2"],
                    "Allowable stress (MPa)": design["allowable_stress_n_mm2"],
                },
                {
                    "Case": "Uplift major-axis bending",
                    "Actual stress (MPa)": design["uplift_major_stress_n_mm2"],
                    "Allowable stress (MPa)": design["allowable_stress_n_mm2"],
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

with advanced_tab:
    st.subheader("Step 5: Effective-width and LTB screening")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Item": "Web reduction factor",
                    "Value": effective_props["web_reduction_factor"],
                },
                {
                    "Item": "Flange reduction factor",
                    "Value": effective_props["flange_reduction_factor"],
                },
                {
                    "Item": "Combined reduction factor",
                    "Value": effective_props["combined_reduction_factor"],
                },
                {
                    "Item": "Advanced effective Ixx",
                    "Value": effective_props["effective_ixx_cm4"],
                },
                {
                    "Item": "Advanced effective Zxx",
                    "Value": effective_props["effective_zxx_cm3"],
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

    ltb_col, biaxial_col = st.columns(2)
    with ltb_col:
        st.subheader("LTB screening")
        st.metric("Allowable stress", f"{ltb_result['allowable_stress_mpa']:.2f} MPa")
        st.metric("Actual stress", f"{ltb_result['actual_stress_mpa']:.2f} MPa")
        st.metric("Slenderness λ", f"{ltb_result['slenderness_ratio_lambda']:.1f}")
        st.write(f"Failure mode / range: **{ltb_result['failure_mode']}**")
        show_status_message(
            ltb_result["is_safe"],
            "LTB screening passes for the submitted restraint assumptions.",
            "LTB screening needs review. Reduce unbraced length, increase section capacity or revise assumptions.",
        )

    with biaxial_col:
        st.subheader("Biaxial bending")
        st.metric(
            "Major-axis utilization", f"{interaction['major_axis_utilization']:.1%}"
        )
        st.metric(
            "Minor-axis utilization", f"{interaction['minor_axis_utilization']:.1%}"
        )
        st.metric("Interaction ratio", f"{interaction['interaction_ratio']:.3f}")
        st.write(f"Governing direction: **{interaction['governer']}**")
        show_status_message(
            interaction["is_safe"],
            "Biaxial interaction passes the screening equation.",
            "Biaxial interaction exceeds the screening limit and needs review.",
        )

    st.subheader("Step 6: Deflection checks")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Load case": "Live load",
                    "Actual deflection (mm)": live_deflection["actual_deflection_mm"],
                    "Limit (mm)": live_deflection["limit_deflection_mm"],
                    "Utilization": f"{live_deflection['utilization_ratio']:.1%}",
                    "Status": status_label(live_deflection["is_safe"]),
                },
                {
                    "Load case": "Wind load",
                    "Actual deflection (mm)": wind_deflection["actual_deflection_mm"],
                    "Limit (mm)": wind_deflection["limit_deflection_mm"],
                    "Utilization": f"{wind_deflection['utilization_ratio']:.1%}",
                    "Status": status_label(wind_deflection["is_safe"]),
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Step 7: Support connection screening")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Item": "Design support shear",
                    "Value": connection_result["design_shear_kn"],
                    "Unit": "kN",
                },
                {
                    "Item": "Bolt shear capacity",
                    "Value": connection_result["bolt_shear_capacity_kn"],
                    "Unit": "kN",
                },
                {
                    "Item": "Bearing capacity",
                    "Value": connection_result["bearing_capacity_kn"],
                    "Unit": "kN",
                },
                {
                    "Item": "Governing capacity",
                    "Value": connection_result["governing_capacity_kn"],
                    "Unit": "kN",
                },
                {
                    "Item": "Utilization",
                    "Value": connection_result["utilization_ratio"],
                    "Unit": "ratio",
                },
                {
                    "Item": "Governing mode",
                    "Value": connection_result["governing_mode"],
                    "Unit": "-",
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

with references_tab:
    st.subheader("Step 8: Code-reference notes")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Design item": "Cold-formed element flat-width ratios",
                    "Reference": "IS 801:1975 Clause 5.2",
                    "How used here": "Flags web and flange width-to-thickness ratios.",
                },
                {
                    "Design item": "Effective width of compression elements",
                    "Reference": "IS 801:1975 Clause 5.2.1",
                    "How used here": "Provides reduction factors for screening effective properties.",
                },
                {
                    "Design item": "Bending stress and LTB review",
                    "Reference": "IS 801:1975 Clause 6.3",
                    "How used here": "Screens bending stress with restraint assumptions.",
                },
                {
                    "Design item": "Combined biaxial bending",
                    "Reference": "IS 801:1975 Clause 6.7",
                    "How used here": "Checks major-plus-minor bending interaction.",
                },
                {
                    "Design item": "Dead, live and wind load inputs",
                    "Reference": "IS 875 Parts 1, 2 and 3",
                    "How used here": "Converts service pressures into purlin line loads.",
                },
                {
                    "Design item": "Support fasteners",
                    "Reference": "IS 1367 / IS 800 guidance",
                    "How used here": "Screens bolt shear and purlin bearing at supports.",
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    st.warning(
        "This is not a certified design package. Confirm the governing code edition, load combinations, "
        "effective widths, local buckling, torsion, restraint detailing, connections and project criteria before issuing calculations."
    )
