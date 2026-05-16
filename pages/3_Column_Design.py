"""Future column design page placeholder."""

import streamlit as st

st.set_page_config(page_title="Column Design - Future Work", layout="wide")

st.title("Column Design")
st.caption("Future-work page retained for navigation planning. No column calculations run yet.")

st.info(
    "Column design is intentionally not active in this version. The future workflow can add axial, "
    "bending, slenderness, base plate and anchor bolt checks when the design criteria are ready."
)

with st.form("future_column_inputs"):
    st.subheader("Future input placeholders")
    col1, col2, col3 = st.columns(3)
    with col1:
        axial_load = st.number_input("Axial load (kN)", value=0.0)
        moment_major = st.number_input("Major-axis moment (kN-m)", value=0.0)
    with col2:
        effective_length = st.number_input("Effective length (m)", min_value=0.0, value=0.0)
        k_factor = st.number_input("Effective length factor, K", min_value=0.0, value=0.0)
    with col3:
        section = st.text_input("Trial column section", value="")
        fy = st.number_input("Steel grade Fy (MPa)", min_value=0.0, value=0.0)

    submitted = st.form_submit_button("Preview future column inputs")

if submitted:
    st.write(
        {
            "Axial load (kN)": axial_load,
            "Major-axis moment (kN-m)": moment_major,
            "Effective length (m)": effective_length,
            "K factor": k_factor,
            "Trial section": section,
            "Fy (MPa)": fy,
            "Status": "Placeholder only - column design checks are not connected yet.",
        }
    )

st.markdown(
    """
### Planned column workflow
- Axial compression and combined axial-plus-bending checks.
- Slenderness and effective-length review.
- Base plate and anchor bolt design placeholders.
- Report-ready summary tables with applicable code references.
"""
)
