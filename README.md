# Cold-Formed Purlin / Girt / Column Design Streamlit App

This Streamlit app provides preliminary cold-formed steel member design workflows.
The Purlin page integrates input collection, preliminary design and
gross/effective-property checks in a single IS 801:1975 Allowable Stress Design
(ASD) workflow for lipped Z-purlins, while the Girt page retains the workbook-derived
calculation scaffold.

## Purlin design workflow

1. Complete one form for material, span, spacing, slope, trial section, service loads and design provision factors.
2. Submit the form to run analysis and design checks together on one page.
3. Check simplified IS 801:1975 Clause 5.2 flat-width ratios:
   - Web flat-width ratio limit: `h/t ≤ 150`
   - Flange flat-width ratio limit for simple lips: `w/t ≤ 60`
4. Resolve gravity `(DL + LL)` and uplift `(DL + WL)` service loads into normal and tangential components on the roof slope.
5. Estimate preliminary continuous-span bending moments:
   - Normal loading: `WL² / 10`
   - Tangential loading: `WL² / 8`
6. Review gross/effective section properties, LTB/restraint factors and biaxial interaction checks with IS 801:1975 Clause 5.2.1, 6.3 and 6.7 references.

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
