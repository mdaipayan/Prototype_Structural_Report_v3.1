# Purlin / Girt / Column Design Streamlit App

This app was generated from the uploaded Excel workbook:
`4. PURLIN_GIRT DESIGN - AIR Concourse - 15.02.2024(1).xlsx`.

## Workbook sheets identified

- `PURLIN DESIGN FOR END BAY`
- `PURLIN DESIGN `
- `GIRT DESIGN FOR END BAY`
- `GIRT DESIGN `

## Extracted purlin design steps

1. Input building geometry: span, bay spacing/effective length, purlin spacing and roof slope.
2. Input loads: dead load, collateral load, live load, wind load, pressure coefficient and steel grade.
3. Calculate slope factors: `Kx = X / sqrt(X² + Y²)` and `Ky = Y / sqrt(X² + Y²)`.
4. Calculate gravity load combination: `(DL + LL + CL) × purlin spacing × Kx`.
5. Calculate wind combination: `(WL × Cp − DL × Kx) × purlin spacing`.
6. Calculate span and support moments using workbook coefficients:
   - End bay: `Mspan = 0.0772 W L²`, `Msupport = 0.1071 W L²`
   - Regular bay / mid bay: `Mspan = 0.0364 W L²`, `Msupport = 0.0714 W L²`
7. Trial a Z-section with thickness, depth, flanges and lips.
8. Compute clear web depth, centroid, moment of inertia, section moduli, area and weight.
9. Check IS 801 rules included in the workbook:
   - Overall depth `< 150t`
   - Minimum depth rule with lower bound `4.8t`
   - Effective-width related checks
   - Basic design stress `0.6 Fy`
10. Calculate actual bending stresses at support and mid-span and report OK/NOT OK.

## App structure

```text
purlin_girt_streamlit_app/
├── app.py
├── design_calcs.py
├── requirements.txt
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

- The app is a reusable calculation scaffold, not a certified design package.
- Section-property calculations are approximated from the workbook intent and should be verified against manufacturer data or dedicated cold-formed design software before issuing drawings/calculations.
- Column Design is intentionally scaffolded for future use.
