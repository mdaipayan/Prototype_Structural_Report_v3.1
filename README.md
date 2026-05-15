# Cold-Formed Purlin / Girt / Column Design Streamlit App

This Streamlit app provides preliminary cold-formed steel member design workflows.
The Purlin page has been rebuilt around an IS 801:1975 Allowable Stress Design
(ASD) screening workflow for lipped Z-purlins, while the Girt page retains the
workbook-derived calculation scaffold.

## Purlin design workflow

1. Input material strength, purlin span, purlin spacing and roof slope.
2. Input the trial lipped Z-profile dimensions: total depth, flange width, lip depth and thickness.
3. Input service dead, live and wind uplift loads in kN/m².
4. Check simplified IS 801:1975 Clause 5.2 flat-width ratios:
   - Web flat-width ratio limit: `h/t ≤ 150`
   - Flange flat-width ratio limit for simple lips: `w/t ≤ 60`
5. Resolve gravity `(DL + LL)` and uplift `(DL + WL)` service loads into normal and tangential components on the roof slope.
6. Estimate preliminary continuous-span bending moments:
   - Normal loading: `WL² / 10`
   - Tangential loading: `WL² / 8`
7. Use the included effective-width framework as the next step before final stress, lateral-torsional buckling and biaxial interaction checks.

## Girt design workflow

The Girt page remains a reusable workbook-based scaffold for dead and wind load
checks, unbraced-length moments and trial Z-section stress checks.

## App structure

```text
purlin_girt_streamlit_app/
├── app.py
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
- Column Design is intentionally scaffolded for future use.
