import streamlit as st

st.set_page_config(page_title="Cold-Formed Member Design", layout="wide")

st.title("Cold-Formed Purlin, Girt & Column Design App")
st.caption(
    "Preliminary cold-formed steel member checks for roof and wall framing workflows."
)

st.markdown("""
### Integrated Z-purlin design workflow (IS 801:1975 ASD framework)
1. Complete one input form for material, framing, section dimensions, service loads and design provision factors.
2. Submit the form to run preliminary design checks and gross/effective-property design checks on the same page.
3. Check IS 801:1975 flat-width limits for the web and flange edge stiffener.
4. Resolve IS 875 dead, imposed and wind loads into normal and tangential roof components.
5. Estimate continuous-span major-axis and minor-axis moments for preliminary screening.
6. Review effective-section, LTB/restraint and biaxial interaction checks with code-reference guidance.

Use the left navigation to open the dedicated Purlin, Girt and Column pages.
""")

st.warning(
    "This app is a calculation scaffold for preliminary screening. Final designs must be verified "
    "against the applicable code clauses, project criteria and approved section properties."
)
