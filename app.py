import streamlit as st

st.set_page_config(page_title="Purlin / Girt / Column Design", layout="wide")

st.title("Cold-Formed Purlin, Girt & Column Design App")
st.caption("Created from the uploaded Excel workbook: PURLIN_GIRT DESIGN - AIR Concourse - 15.02.2024")

st.markdown(
    """
### Extracted purlin design workflow
1. Enter building span, bay spacing/effective length, purlin spacing, roof slope, DL, CL, LL, WL, wind pressure coefficient and steel grade.
2. Calculate roof slope factors `Kx` and `Ky`.
3. Calculate load combinations: `(DL + LL + CL) × spacing × Kx` and `(WL × Cp − DL × Kx) × spacing`.
4. Calculate positive span moment and negative support moment using workbook coefficients.
5. Select/trial a Z-section and calculate clear web depth, centroid, inertia, section moduli, area and unit weight.
6. Check IS 801 limits: overall depth, minimum depth and effective-width related limits.
7. Calculate permissible bending stress and actual bending stresses at support/span.
8. Report OK/NOT OK checks and revise section if needed.

Use the left navigation to open separate Purlin, Girt, and Column pages.
"""
)

st.info("Column Design is scaffolded for future use, as requested. Add formulas in `design_calcs.py` and UI fields in `pages/3_Column_Design.py`.")
