import pandas as pd
import streamlit as st
from design_calcs import (
    LoadInputs,
    ZSectionInputs,
    PURLIN_END_BAY_COEFF,
    PURLIN_MID_BAY_COEFF,
    purlin_loads,
    purlin_moments,
    z_section_properties,
    code_checks,
)

st.set_page_config(page_title="Purlin Design", layout="wide")
st.title("Purlin Design")

with st.sidebar:
    st.header("Design type")
    design_type = st.selectbox("Bay condition", ["End Bay", "Regular / Mid Bay"])
    coeff = PURLIN_END_BAY_COEFF if design_type == "End Bay" else PURLIN_MID_BAY_COEFF

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Geometry & Loads")
    span = st.number_input("Span of building (m)", value=35.5)
    bay = st.number_input("Bay spacing L (m)", value=9.347)
    spacing = st.number_input("Purlin spacing Ps (m)", value=1.5)
    slope_x = st.number_input("Roof slope X", value=10.0)
    slope_y = st.number_input("Roof slope Y", value=1.0)
with col2:
    st.subheader("Load intensities")
    dl = st.number_input("Dead load DL (kg/m²)", value=15.0)
    cl = st.number_input("Collateral load CL (kg/m²)", value=75.0)
    ll = st.number_input("Live load LL (kg/m²)", value=75.0)
    wl = st.number_input("Wind load WL (kg/m²)", value=130.0)
    cp = st.number_input("Wind pressure coefficient Cp", value=1.4)
with col3:
    st.subheader("Trial Z-section")
    fy = st.number_input("Steel grade Fy (MPa)", value=345.0)
    t = st.number_input("Thickness t (mm)", value=2.5)
    D = st.number_input("Overall depth D (mm)", value=250.0)
    b1 = st.number_input("Flange b1 (mm)", value=64.0)
    b2 = st.number_input("Flange b2 (mm)", value=66.0)
    l1 = st.number_input("Lip L1 (mm)", value=20.0)
    l2 = st.number_input("Lip L2 (mm)", value=20.0)

inp = LoadInputs(
    span_m=span,
    bay_spacing_m=bay,
    purlin_or_girt_spacing_m=spacing,
    roof_slope_x=slope_x,
    roof_slope_y=slope_y,
    dead_load_kg_m2=dl,
    collateral_load_kg_m2=cl,
    live_load_kg_m2=ll,
    wind_load_kg_m2=wl,
    wind_pressure_coeff=cp,
    fy_mpa=fy,
)
sec = ZSectionInputs(
    t_mm=t,
    overall_depth_D_mm=D,
    b1_mm=b1,
    b2_mm=b2,
    lip1_mm=l1,
    lip2_mm=l2,
)
loads = purlin_loads(inp)
moments = purlin_moments(inp, coeff)
props = z_section_properties(sec)
checks = code_checks(
    inp,
    sec,
    props,
    moments["gravity_support_moment_kg_m"],
    moments["gravity_span_moment_kg_m"],
)

st.divider()
load_cols = st.columns(4)
load_cols[0].metric("Kx", f"{loads['kx']:.4f}")
load_cols[1].metric(
    "Gravity load", f"{loads['gravity_load_kg_m']:.2f} kg/m", loads["gravity_direction"]
)
load_cols[2].metric(
    "Wind net load", f"{loads['wind_net_load_kg_m']:.2f} kg/m", loads["wind_direction"]
)
load_cols[3].metric("Coefficient set", f"{coeff.span} / {coeff.support}")

st.subheader("Moments")
st.dataframe(
    pd.DataFrame([moments]).T.rename(columns={0: "Value"}), use_container_width=True
)

st.subheader("Section properties")
st.dataframe(
    pd.DataFrame([props]).T.rename(columns={0: "Value"}), use_container_width=True
)

st.subheader("Checks")
check_df = pd.DataFrame(
    [
        {
            "Check": "Overall depth < 150t",
            "Limit/Value": f"{sec.overall_depth_D_mm:.1f} < {checks['overall_depth_limit_mm']:.1f} mm",
            "Status": "OK" if checks["overall_depth_ok"] else "NOT OK",
        },
        {
            "Check": "Minimum clear web depth",
            "Limit/Value": (
                f"{props['d_clear_mm']:.1f} ≥ "
                f"{checks['minimum_depth_required_mm']:.1f} mm"
            ),
            "Status": "OK" if checks["minimum_depth_check_ok"] else "NOT OK",
        },
        {
            "Check": "Support bending stress",
            "Limit/Value": f"{checks['support_actual_stress_n_mm2']:.2f} ≤ {checks['basic_design_stress_n_mm2']:.2f} N/mm²",
            "Status": "OK" if checks["support_stress_ok"] else "NOT OK",
        },
        {
            "Check": "Span bending stress",
            "Limit/Value": f"{checks['span_actual_stress_n_mm2']:.2f} ≤ {checks['basic_design_stress_n_mm2']:.2f} N/mm²",
            "Status": "OK" if checks["span_stress_ok"] else "NOT OK",
        },
    ]
)
st.dataframe(check_df, use_container_width=True, hide_index=True)

st.warning(
    "Verify final design against IS 801 and project/client criteria before issue. This app is a reusable calculation scaffold extracted from the workbook."
)
