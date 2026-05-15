import streamlit as st

st.set_page_config(page_title="Cold-Formed Member Design", layout="wide")

st.title("Cold-Formed Purlin, Girt & Column Design App")
st.caption(
    "Preliminary cold-formed steel member checks for roof and wall framing workflows."
)

st.markdown("""
### Z-purlin design workflow (IS 801:1975 ASD framework)
1. Enter material strength, purlin span, purlin spacing and roof slope.
2. Enter trial lipped Z-profile dimensions: total depth, flange width, lip depth and thickness.
3. Enter service dead, live and wind uplift loads in kN/m².
4. Check preliminary flat-width ratios for the web and flange edge stiffener limits.
5. Resolve gravity and uplift loads into normal and tangential components on the roof slope.
6. Estimate continuous-span major-axis and minor-axis moments for preliminary screening.
7. Use the effective-width and stress-check framework as the next step before issuing calculations.

Use the left navigation to open the dedicated Purlin, Girt and Column pages.
""")

st.warning(
    "This app is a calculation scaffold for preliminary screening. Final designs must be verified "
    "against the applicable code clauses, project criteria and approved section properties."
)
