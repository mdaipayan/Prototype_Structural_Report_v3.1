import streamlit as st

st.set_page_config(page_title="Cold-Formed Member Design", layout="wide")

st.title("Cold-Formed Member Design App")
st.caption("Complete Z-purlin design now, with Girt and Column pages retained for future work.")

st.markdown(
    """
### Current scope

The active design workflow is the **Complete Z-Purlin Design** page. It is organized step by step with
IS 801:1975 and IS 875 references beside the relevant checks.

Use the left navigation for:

1. **Purlin Design** — active workflow with inputs, load resolution, moment checks, section/stress checks,
   LTB, biaxial bending, deflection, connection screening and references.
2. **Girt Design** — future-work placeholder only; no girt design checks are currently run.
3. **Column Design** — future-work placeholder only; no column design checks are currently run.
"""
)

st.warning(
    "This app is a calculation scaffold for preliminary screening. Final designs must be verified "
    "against the applicable code clauses, project criteria and approved section properties."
)
