import pandas as pd
import streamlit as st
from design_calcs import LoadInputs, ZSectionInputs, girt_loads, girt_moments, z_section_properties, code_checks

st.set_page_config(page_title="Girt Design", layout="wide")
st.title("Girt Design")

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Geometry")
    span = st.number_input("Span of building (m)", value=35.5)
    bay = st.number_input("Bay spacing L (m)", value=9.347)
    spacing = st.number_input("Girt spacing Ps (m)", value=1.5)
    sag_bars = st.number_input("Number of sag bars", value=4, step=1)
with col2:
    st.subheader("Loads")
    dl = st.number_input("Dead load DL (kg/m²)", value=15.0)
    wl = st.number_input("Wind load WL (kg/m²)", value=130.0)
    cp = st.number_input("Wind pressure coefficient Cp", value=1.4)
    fy = st.number_input("Steel grade Fy (MPa)", value=345.0)
with col3:
    st.subheader("Trial Z-section")
    t = st.number_input("Thickness t (mm)", value=2.0)
    D = st.number_input("Overall depth D (mm)", value=250.0)
    b1 = st.number_input("Flange b1 (mm)", value=64.0)
    b2 = st.number_input("Flange b2 (mm)", value=66.0)
    l1 = st.number_input("Lip L1 (mm)", value=20.0)
    l2 = st.number_input("Lip L2 (mm)", value=20.0)

inp = LoadInputs(span, bay, spacing, 10.0, 1.0, dl, 0.0, 0.0, wl, cp, fy, int(sag_bars))
sec = ZSectionInputs(t, D, b1, b2, l1, l2)
loads = girt_loads(inp)
moments = girt_moments(inp)
props = z_section_properties(sec)
checks = code_checks(inp, sec, props, moments["wind_support_moment_kg_m"], moments["wind_span_moment_kg_m"])

st.divider()
cols = st.columns(4)
cols[0].metric("Dead load", f"{loads['dead_load_kg_m']:.2f} kg/m")
cols[1].metric("Wind load", f"{loads['wind_load_kg_m']:.2f} kg/m")
cols[2].metric("Unbraced length", f"{moments['unbraced_length_m']:.3f} m")
cols[3].metric("Basic stress", f"{checks['basic_design_stress_n_mm2']:.1f} N/mm²")

st.subheader("Moments")
st.dataframe(pd.DataFrame([moments]).T.rename(columns={0: "Value"}), use_container_width=True)

st.subheader("Section properties")
st.dataframe(pd.DataFrame([props]).T.rename(columns={0: "Value"}), use_container_width=True)

st.subheader("Checks")
st.dataframe(pd.DataFrame([
    {"Check": "Overall depth < 150t", "Limit/Value": f"{sec.overall_depth_D_mm:.1f} < {checks['overall_depth_limit_mm']:.1f} mm", "Status": "OK" if checks['overall_depth_ok'] else "NOT OK"},
    {"Check": "Support bending stress under wind", "Limit/Value": f"{checks['support_actual_stress_n_mm2']:.2f} ≤ {checks['basic_design_stress_n_mm2']:.2f} N/mm²", "Status": "OK" if checks['support_stress_ok'] else "NOT OK"},
    {"Check": "Span bending stress under wind", "Limit/Value": f"{checks['span_actual_stress_n_mm2']:.2f} ≤ {checks['basic_design_stress_n_mm2']:.2f} N/mm²", "Status": "OK" if checks['span_stress_ok'] else "NOT OK"},
]), use_container_width=True, hide_index=True)

st.info("This page is separate from Purlin Design and can be extended with cladding side-rail cases, openings, or project-specific coefficients.")
