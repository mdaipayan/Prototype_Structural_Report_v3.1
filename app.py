import streamlit as st

st.set_page_config(page_title="Complete Z-Purlin Design", layout="wide")

<<<<<<< HEAD
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
=======
st.title("Complete Cold-Formed Z-Purlin Design App")
st.caption("A focused, user-friendly Streamlit workflow for Z-purlin design only.")

st.markdown(
    """
### What this app does now

This app is intentionally focused on **one complete Z-purlin design workflow**.
Girt design, column design and the separate advanced-analysis page have been removed for now so users do not need to decide which page contains the governing checks.

Open **Purlin Design** from the left navigation to run:

1. Material, span, spacing, slope, section and service-load input.
2. IS 801:1975 flat-width checks for web and flange elements.
3. IS 875 load resolution into normal and tangential roof components.
4. Preliminary continuous-span bending moments.
5. Gross/effective section-property and ASD stress checks.
6. Effective-width, LTB, biaxial bending, deflection and connection screening.
7. User-friendly pass/review summaries and code-reference notes.
>>>>>>> main
"""
)

st.warning(
    "This app is a calculation scaffold for preliminary screening. Final designs must be verified "
    "against the applicable code clauses, project criteria and approved section properties."
)
