import streamlit as st

st.set_page_config(page_title="Column Design", layout="wide")
st.title("Column Design")

st.info("Future-use page scaffold. Add column design formulas in `design_calcs.py` and connect them here.")

with st.form("column_placeholder"):
    st.subheader("Basic future inputs")
    axial_load = st.number_input("Factored / service axial load", value=0.0)
    column_length = st.number_input("Column effective length (m)", value=0.0)
    section = st.text_input("Trial section", value="")
    fy = st.number_input("Steel grade Fy (MPa)", value=345.0)
    submitted = st.form_submit_button("Save / Preview")

if submitted:
    st.write({
        "Axial load": axial_load,
        "Effective length": column_length,
        "Trial section": section,
        "Fy": fy,
        "Status": "Placeholder only - no design check connected yet",
    })

st.markdown(
    """
### Suggested next development steps
- Add column section library or manual section-property input.
- Add axial compression and combined axial+bending checks.
- Add slenderness, effective length factor, base plate and anchor bolt pages if required.
"""
)
