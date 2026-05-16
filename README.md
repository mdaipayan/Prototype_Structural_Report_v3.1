# Complete Cold-Formed Z-Purlin Design Streamlit App

This Streamlit app provides a focused, user-friendly workflow for preliminary
cold-formed steel **Z-purlin** design. Girt design, column design and the
previous separate advanced-analysis page are intentionally removed for now; the
full current Z-purlin workflow is shown on the Purlin Design page only.

## Purlin design workflow

1. Complete one guided form for material, span, spacing, slope, trial section,
   service loads, LTB/deflection assumptions and support connection inputs.
2. Submit the form to run all purlin checks together on one page.
3. Review the overall pass/review status cards and summary table.
4. Check simplified IS 801:1975 Clause 5.2 flat-width ratios:
   - Web flat-width ratio limit: `h/t ≤ 150`
   - Flange flat-width ratio limit for simple lips: `w/t ≤ 60`
5. Resolve gravity `(DL + LL)` and uplift `(DL + WL)` service loads into normal
   and tangential components on the roof slope.
6. Estimate preliminary continuous-span bending moments:
   - Normal loading: `WL² / 10`
   - Tangential loading: `WL² / 8`
7. Review gross/effective section properties, ASD stress checks, effective-width
   screening, LTB screening, biaxial interaction, deflection and connection
   screening with code-reference guidance.

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
    └── 1_Purlin_Design.py
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- The app is a reusable preliminary calculation scaffold, not a certified design package.
- Effective-width equations, section-property reductions, lateral-torsional buckling, biaxial interaction, connections and project-specific criteria must be verified before issuing drawings or calculations.
- Girt and column design pages can be added later when those workflows are ready.
