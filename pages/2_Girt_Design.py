"""Future girt design page placeholder."""

import streamlit as st

st.set_page_config(page_title="Girt Design - Future Work", layout="wide")

st.title("Girt Design")
st.caption("Future-work page retained for navigation planning. No girt calculations run yet.")

st.info(
    "Girt design is intentionally not active in this version. The next implementation can add "
    "wall girt load inputs, section properties, wind checks, deflection checks and IS code references."
)

with st.form("future_girt_inputs"):
    st.subheader("Future input placeholders")
    col1, col2, col3 = st.columns(3)
    with col1:
        span = st.number_input("Girt span / bay spacing (m)", min_value=0.0, value=0.0)
        spacing = st.number_input("Girt spacing (m)", min_value=0.0, value=0.0)
    with col2:
        wind = st.number_input("Wall wind pressure (kN/m²)", value=0.0)
        dead = st.number_input("Self/dead load allowance (kN/m²)", value=0.0)
    with col3:
        section = st.text_input("Trial section", value="")
        fy = st.number_input("Steel grade Fy (MPa)", min_value=0.0, value=0.0)

    submitted = st.form_submit_button("Preview future girt inputs")

if submitted:
    st.write(
        {
            "Span / bay spacing (m)": span,
            "Girt spacing (m)": spacing,
            "Wind pressure (kN/m²)": wind,
            "Dead load allowance (kN/m²)": dead,
            "Trial section": section,
            "Fy (MPa)": fy,
            "Status": "Placeholder only - girt design checks are not connected yet.",
        }
    )

st.markdown(
    """
### Planned girt workflow
- Wall wind and dead-load collection.
- Trial cold-formed section properties.
- Strength and serviceability checks with clear code references.
- Report-ready summary tables matching the purlin page style.
"""
)
