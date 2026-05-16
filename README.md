# Cold-Formed Member Design Streamlit App

This Streamlit app currently provides a complete, user-friendly workflow for
preliminary cold-formed steel **Z-purlin** design. Girt and Column pages are
retained as future-work placeholders only; they do not run design checks yet.

## Current page scope

1. **Purlin Design** — active step-by-step Z-purlin workflow with IS 801:1975,
   IS 875 and connection-reference notes.
2. **Girt Design** — future-work placeholder for wall girt design.
3. **Column Design** — future-work placeholder for column design.

## Purlin design workflow

1. Complete one guided form for material, span, spacing, slope, trial section,
   service loads, LTB/deflection assumptions and support connection inputs.
2. Submit the form to run all purlin checks together on one page.
3. Review the overall pass/review status cards, optimal catalog section recommendation and summary table.
4. Check simplified IS 801:1975 Clause 5.2 flat-width ratios:
   - Web flat-width ratio limit: `h/t ≤ 150`
   - Flange flat-width ratio limit for simple lips: `w/t ≤ 60`
5. Resolve gravity `(DL + LL)` and uplift `(DL + WL)` service loads into normal
   and tangential components on the roof slope using IS 875 service-load inputs.
6. Estimate preliminary continuous-span bending moments:
   - Normal loading: `WL² / 10`
   - Tangential loading: `WL² / 8`
7. Review gross/effective section properties, ASD stress checks, effective-width
   screening, LTB screening, biaxial interaction, deflection and connection
   screening with code-reference guidance.
8. Download a step-by-step PDF report with formulas, values, permissible limits, references, the optimal section recommendation and conclusion.

## App structure

```text
purlin_girt_streamlit_app/
├── app.py
├── advanced_checks.py
├── design_calcs.py
├── requirements.txt
├── tests/
│   └── test_design_calcs.py
└── pages/
    ├── 1_Purlin_Design.py
    ├── 2_Girt_Design.py
    └── 3_Column_Design.py
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- The app is a reusable preliminary calculation scaffold, not a certified design package.
- Effective-width equations, section-property reductions, lateral-torsional buckling, biaxial interaction, connections and project-specific criteria must be verified before issuing drawings or calculations.
- Girt and column design checks can be connected later when those workflows are ready.
