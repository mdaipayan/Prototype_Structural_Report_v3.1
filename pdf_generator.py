"""PDF report generator for Z-purlin design calculations.

This module creates professional PDF reports suitable for structural design
documentation and client deliverables, following IS 801:1975 ASD framework.

Units: kN, m, mm, N/mm²
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black, lightgrey
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_z_section_diagram(
    total_depth_h_mm: float,
    flange_width_b_mm: float,
    lip_depth_d_mm: float,
    thickness_t_mm: float,
) -> Image:
    """Generate Z-section cross-section diagram as an embedded image."""
    fig, ax = plt.subplots(figsize=(4, 5), dpi=100)

    # Scale factor for drawing (mm to inches)
    scale = 0.01

    # Define Z-section geometry
    h = total_depth_h_mm * scale
    b = flange_width_b_mm * scale
    d = lip_depth_d_mm * scale
    t = thickness_t_mm * scale

    # Web
    web = patches.Rectangle(
        (t, t),
        t,
        h - 2 * t,
        linewidth=2,
        edgecolor="darkblue",
        facecolor="lightblue",
        alpha=0.7,
    )
    ax.add_patch(web)

    # Top flange
    top_flange = patches.Rectangle(
        (0, h - t),
        b,
        t,
        linewidth=2,
        edgecolor="darkblue",
        facecolor="lightblue",
        alpha=0.7,
    )
    ax.add_patch(top_flange)

    # Bottom flange
    bottom_flange = patches.Rectangle(
        (0, 0),
        b,
        t,
        linewidth=2,
        edgecolor="darkblue",
        facecolor="lightblue",
        alpha=0.7,
    )
    ax.add_patch(bottom_flange)

    # Top lip
    top_lip = patches.Rectangle(
        (b - t, h - t - d),
        t,
        d,
        linewidth=2,
        edgecolor="darkblue",
        facecolor="lightblue",
        alpha=0.7,
    )
    ax.add_patch(top_lip)

    # Bottom lip
    bottom_lip = patches.Rectangle(
        (b - t, t),
        t,
        d,
        linewidth=2,
        edgecolor="darkblue",
        facecolor="lightblue",
        alpha=0.7,
    )
    ax.add_patch(bottom_lip)

    # Add dimensions with arrows
    ax.annotate(
        "",
        xy=(b + 0.3, 0),
        xytext=(b + 0.3, h),
        arrowprops=dict(arrowstyle="<->", color="red", lw=1.5),
    )
    ax.text(
        b + 0.5,
        h / 2,
        f"h={total_depth_h_mm}mm",
        fontsize=9,
        color="red",
        rotation=90,
        va="center",
    )

    ax.annotate(
        "",
        xy=(0, -0.4),
        xytext=(b, -0.4),
        arrowprops=dict(arrowstyle="<->", color="red", lw=1.5),
    )
    ax.text(
        b / 2, -0.6, f"b={flange_width_b_mm}mm", fontsize=9, color="red", ha="center"
    )

    ax.annotate(
        "",
        xy=(b + 0.15, h - t),
        xytext=(b + 0.15, h - t - d),
        arrowprops=dict(arrowstyle="<->", color="green", lw=1.5),
    )
    ax.text(
        b + 0.35,
        h - t - d / 2,
        f"d={lip_depth_d_mm}mm",
        fontsize=8,
        color="green",
        rotation=90,
        va="center",
    )

    ax.text(
        t / 2,
        h / 2,
        f"t={thickness_t_mm}mm",
        fontsize=7,
        color="black",
        ha="center",
        va="center",
        weight="bold",
    )

    ax.set_xlim(-0.2, b + 1.0)
    ax.set_ylim(-0.8, h + 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Z-Section Profile", fontsize=12, weight="bold", pad=10)

    plt.tight_layout()

    # Save to BytesIO
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png", dpi=100, bbox_inches="tight")
    img_buffer.seek(0)
    plt.close(fig)

    return Image(img_buffer, width=2.5 * inch, height=3.0 * inch)


def create_design_report(
    inputs: Dict[str, Any],
    flat_width_checks: Dict[str, Any],
    resolved_loads: Dict[str, Any],
    design_moments: Dict[str, Any],
    design: Optional[Dict[str, Any]] = None,
    effective_props: Optional[Dict[str, Any]] = None,
    ltb_result: Optional[Dict[str, Any]] = None,
    interaction: Optional[Dict[str, Any]] = None,
    live_deflection: Optional[Dict[str, Any]] = None,
    wind_deflection: Optional[Dict[str, Any]] = None,
    connection_result: Optional[Dict[str, Any]] = None,
    optimal_section: Optional[Dict[str, Any]] = None,
    all_ok: Optional[bool] = None,
    project_name: str = "Z-Purlin Design",
    location: str = "Project Location",
    designer: str = "Structural Designer",
) -> bytes:
    """Create a step-by-step PDF report for the submitted Z-purlin design."""

    def fmt(value: Any, digits: int = 3) -> str:
        if isinstance(value, (int, float)):
            return f"{value:.{digits}f}"
        return str(value)

    def status_text(is_ok: bool) -> str:
        return "PASS" if is_ok else "REVIEW"

    def add_table(
        rows: list[list[Any]], col_widths: list[float], header_color: str = "#003366"
    ) -> None:
        table = Table(rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor(header_color)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#CCCCCC")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#F5F5F5")]),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 10))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=HexColor("#003366"),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=HexColor("#003366"),
        spaceAfter=8,
        spaceBefore=10,
        fontName="Helvetica-Bold",
    )
    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=9,
        textColor=black,
        spaceAfter=5,
        leading=11,
    )

    story.append(Paragraph("Z-PURLIN DESIGN REPORT", title_style))
    story.append(
        Paragraph(
            "Step-by-step preliminary design procedure per IS 801:1975 ASD and IS 875 service-load inputs",
            normal_style,
        )
    )
    story.append(Spacer(1, 8))

    add_table(
        [
            ["Project", project_name, "Date", datetime.now().strftime("%Y-%m-%d")],
            ["Location", location, "Designer", designer],
            [
                "Design standard",
                "IS 801:1975 ASD",
                "Load references",
                "IS 875 Parts 1, 2 and 3",
            ],
        ],
        [1.3 * inch, 2.0 * inch, 1.3 * inch, 2.0 * inch],
        "#336699",
    )

    story.append(Paragraph("1. Input data and trial section", heading_style))
    add_table(
        [
            ["Parameter", "Expression / source", "Value", "Unit"],
            ["Yield strength, Fy", "User input", fmt(inputs["fy_mpa"], 1), "MPa"],
            ["Span, L", "User input", fmt(inputs["span_m"], 2), "m"],
            ["Purlin spacing, s", "User input", fmt(inputs["spacing_m"], 3), "m"],
            ["Roof slope, theta", "User input", fmt(inputs["slope_deg"], 1), "deg"],
            [
                "Dead load, DL",
                "IS 875 Part 1 input",
                fmt(inputs["dead_load_kn_m2"], 3),
                "kN/m2",
            ],
            [
                "Live load, LL",
                "IS 875 Part 2 input",
                fmt(inputs["live_load_kn_m2"], 3),
                "kN/m2",
            ],
            [
                "Wind load, WL",
                "IS 875 Part 3 input",
                fmt(inputs["wind_load_kn_m2"], 3),
                "kN/m2",
            ],
            [
                "Trial section",
                "h x b x d x t",
                f"{fmt(inputs['total_depth_h_mm'], 1)} x {fmt(inputs['flange_width_b_mm'], 1)} x {fmt(inputs['lip_depth_d_mm'], 1)} x {fmt(inputs['thickness_t_mm'], 2)}",
                "mm",
            ],
        ],
        [1.7 * inch, 2.2 * inch, 1.5 * inch, 1.0 * inch],
    )

    story.append(Paragraph("Trial Z-section profile", normal_style))
    try:
        story.append(
            generate_z_section_diagram(
                inputs["total_depth_h_mm"],
                inputs["flange_width_b_mm"],
                inputs["lip_depth_d_mm"],
                inputs["thickness_t_mm"],
            )
        )
    except Exception as exc:
        story.append(Paragraph(f"Section diagram unavailable: {exc}", normal_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Flat-width ratio checks", heading_style))
    story.append(
        Paragraph(
            "Reference: IS 801:1975 Clause 5.2. Web flat width = h - 2t; flange flat width = b - 2t. "
            "Permissible screening limits used by this app are web ratio <= 150 and lipped flange ratio <= 60.",
            normal_style,
        )
    )
    add_table(
        [
            ["Check", "Formula / expression", "Actual", "Permissible limit", "Status"],
            [
                "Web flat-width ratio",
                "(h - 2t) / t",
                fmt(flat_width_checks["web_ratio"], 2),
                f"<= {fmt(flat_width_checks['web_ratio_limit'], 0)}",
                status_text(flat_width_checks["web_ratio_ok"]),
            ],
            [
                "Flange flat-width ratio",
                "(b - 2t) / t",
                fmt(flat_width_checks["flange_ratio"], 2),
                f"<= {fmt(flat_width_checks['flange_ratio_limit'], 0)}",
                status_text(flat_width_checks["flange_ratio_ok"]),
            ],
        ],
        [1.7 * inch, 2.1 * inch, 1.0 * inch, 1.3 * inch, 0.9 * inch],
        "#660033",
    )

    story.append(Paragraph("3. Load resolution on roof slope", heading_style))
    story.append(
        Paragraph(
            "Reference: IS 875 service loads. Line loads are area loads multiplied by spacing. "
            "Gravity load = DL + LL; uplift load = DL + WL. Components are resolved by cos(theta) normal to the roof and sin(theta) tangential to the roof.",
            normal_style,
        )
    )
    add_table(
        [
            ["Load component", "Expression", "Value", "Unit"],
            [
                "Dead line load",
                "DL x s",
                fmt(resolved_loads["dead_line_load_kn_m"], 4),
                "kN/m",
            ],
            [
                "Live line load",
                "LL x s",
                fmt(resolved_loads["live_line_load_kn_m"], 4),
                "kN/m",
            ],
            [
                "Wind line load",
                "WL x s",
                fmt(resolved_loads["wind_line_load_kn_m"], 4),
                "kN/m",
            ],
            [
                "Gravity normal",
                "(DL + LL) x s x cos(theta)",
                fmt(resolved_loads["gravity_normal_kn_m"], 4),
                "kN/m",
            ],
            [
                "Gravity tangential",
                "(DL + LL) x s x sin(theta)",
                fmt(resolved_loads["gravity_tangential_kn_m"], 4),
                "kN/m",
            ],
            [
                "Uplift normal",
                "(DL + WL) x s x cos(theta)",
                fmt(resolved_loads["uplift_normal_kn_m"], 4),
                "kN/m",
            ],
            [
                "Uplift tangential",
                "(DL + WL) x s x sin(theta)",
                fmt(resolved_loads["uplift_tangential_kn_m"], 4),
                "kN/m",
            ],
        ],
        [1.7 * inch, 2.7 * inch, 1.2 * inch, 0.9 * inch],
    )

    story.append(
        Paragraph("4. Preliminary continuous-span bending moments", heading_style)
    )
    story.append(
        Paragraph(
            "Moment expressions used for preliminary screening: Mmajor = w_normal L^2 / n_normal and Mminor = w_tangential L^2 / n_tangential. "
            "The denominator values are user inputs so project-specific continuity assumptions can be reviewed.",
            normal_style,
        )
    )
    add_table(
        [
            ["Case", "Expression", "Value", "Unit"],
            [
                "Gravity major-axis",
                "w_gravity,normal x L^2 / n_normal",
                fmt(design_moments["gravity_major_axis_kn_m"], 4),
                "kN-m",
            ],
            [
                "Gravity minor-axis",
                "w_gravity,tangential x L^2 / n_tangential",
                fmt(design_moments["gravity_minor_axis_kn_m"], 4),
                "kN-m",
            ],
            [
                "Uplift major-axis",
                "w_uplift,normal x L^2 / n_normal",
                fmt(design_moments["uplift_major_axis_kn_m"], 4),
                "kN-m",
            ],
            [
                "Normal denominator",
                "n_normal",
                fmt(design_moments["normal_moment_denominator"], 2),
                "-",
            ],
            [
                "Tangential denominator",
                "n_tangential",
                fmt(design_moments["tangential_moment_denominator"], 2),
                "-",
            ],
        ],
        [1.7 * inch, 2.8 * inch, 1.2 * inch, 0.8 * inch],
    )

    if design:
        story.append(
            Paragraph("5. Section properties and ASD stress checks", heading_style)
        )
        story.append(
            Paragraph(
                "Reference: IS 801:1975 bending stress screening. Allowable stress used by the app = 0.6 Fy x LTB reduction factor. "
                "Bending stress expression: f = M / Z, with kN-m converted to N-mm and cm3 converted to mm3.",
                normal_style,
            )
        )
        add_table(
            [
                ["Item", "Expression / basis", "Value", "Limit / unit"],
                [
                    "Gross area",
                    "Calculated from thin-walled Z geometry",
                    fmt(design["area_cm2"], 3),
                    "cm2",
                ],
                [
                    "Weight",
                    "Area x steel density",
                    fmt(design["weight_kg_m"], 3),
                    "kg/m",
                ],
                [
                    "Effective Zxx",
                    "Gross Zxx x effective factor",
                    fmt(design["zxx_effective_cm3"], 3),
                    "cm3",
                ],
                [
                    "Effective Zyy",
                    "Gross Zyy x effective factor",
                    fmt(design["zyy_effective_cm3"], 3),
                    "cm3",
                ],
                [
                    "Allowable stress",
                    "0.6 Fy x reduction factor",
                    fmt(design["allowable_stress_n_mm2"], 2),
                    "MPa",
                ],
                [
                    "Gravity interaction",
                    "(fx + fy) / Fallow",
                    fmt(design["gravity_interaction_ratio"], 3),
                    f"<= 1.000 {status_text(design['gravity_interaction_ok'])}",
                ],
                [
                    "Uplift interaction",
                    "fuplift / Fallow",
                    fmt(design["uplift_interaction_ratio"], 3),
                    f"<= 1.000 {status_text(design['uplift_interaction_ok'])}",
                ],
            ],
            [1.5 * inch, 2.4 * inch, 1.3 * inch, 1.4 * inch],
            "#336699",
        )

    if effective_props or ltb_result or interaction:
        story.append(
            Paragraph("6. Effective width, LTB and biaxial checks", heading_style)
        )
        advanced_rows = [
            ["Check", "Expression / reference", "Actual", "Permissible limit / status"]
        ]
        if effective_props:
            advanced_rows.extend(
                [
                    [
                        "Effective web factor",
                        "IS 801:1975 Clause 5.2.1 screening",
                        fmt(effective_props["web_reduction_factor"], 3),
                        "<= 1.000",
                    ],
                    [
                        "Effective flange factor",
                        "IS 801:1975 Clause 5.2.1 screening",
                        fmt(effective_props["flange_reduction_factor"], 3),
                        "<= 1.000",
                    ],
                    [
                        "Effective Ixx",
                        "Gross Ixx x combined reduction factor",
                        fmt(effective_props["effective_ixx_cm4"], 3),
                        "cm4",
                    ],
                ]
            )
        if ltb_result:
            advanced_rows.extend(
                [
                    [
                        "LTB slenderness",
                        "K x Lu / ry",
                        fmt(ltb_result["slenderness_ratio_lambda"], 2),
                        "Review against IS 801 bending restraint guidance",
                    ],
                    [
                        "LTB utilization",
                        "Actual bending stress / LTB allowable stress",
                        f"{ltb_result['utilization_ratio']:.1%}",
                        f"<= 100% {status_text(ltb_result['is_safe'])}",
                    ],
                ]
            )
        if interaction:
            advanced_rows.append(
                [
                    "Biaxial interaction",
                    "Power-law combined major/minor bending",
                    fmt(interaction["interaction_ratio"], 3),
                    f"<= 1.000 {status_text(interaction['is_safe'])}",
                ]
            )
        add_table(
            advanced_rows, [1.6 * inch, 2.8 * inch, 1.2 * inch, 1.6 * inch], "#003366"
        )

    if live_deflection or wind_deflection or connection_result:
        story.append(
            Paragraph("7. Serviceability and support connection checks", heading_style)
        )
        service_rows = [
            [
                "Check",
                "Formula / basis",
                "Actual demand",
                "Permissible limit / capacity",
            ]
        ]
        if live_deflection:
            service_rows.append(
                [
                    "Live-load deflection",
                    "delta = CwL^4 / EI",
                    f"{fmt(live_deflection['actual_deflection_mm'], 2)} mm",
                    f"<= {fmt(live_deflection['limit_deflection_mm'], 2)} mm {status_text(live_deflection['is_safe'])}",
                ]
            )
        if wind_deflection:
            service_rows.append(
                [
                    "Wind-load deflection",
                    "delta = CwL^4 / EI",
                    f"{fmt(wind_deflection['actual_deflection_mm'], 2)} mm",
                    f"<= {fmt(wind_deflection['limit_deflection_mm'], 2)} mm {status_text(wind_deflection['is_safe'])}",
                ]
            )
        if connection_result:
            service_rows.append(
                [
                    "Support connection shear",
                    "V = max(|wL/2|); capacity = min(bolt shear, purlin bearing)",
                    f"{fmt(connection_result['design_shear_kn'], 2)} kN",
                    f"{fmt(connection_result['governing_capacity_kn'], 2)} kN {status_text(connection_result['is_safe'])}",
                ]
            )
        add_table(
            service_rows, [1.6 * inch, 3.0 * inch, 1.2 * inch, 1.8 * inch], "#660033"
        )

    story.append(Paragraph("8. Optimal section recommendation", heading_style))
    if optimal_section and optimal_section.get("section"):
        section = optimal_section["section"]
        optimal_status = (
            "passes all included screening checks"
            if optimal_section.get("passes")
            else "is the closest catalog option but still needs review"
        )
        story.append(
            Paragraph(
                f"The app searched the built-in trial catalog and selected the lightest section that {optimal_status}. "
                "Optimization objective: minimum calculated weight among candidate Z-sections using the same loads, supports, connection assumptions and permissible limits as the submitted design.",
                normal_style,
            )
        )
        add_table(
            [
                [
                    "Recommended section",
                    "Weight",
                    "Governing utilization",
                    "Conclusion",
                ],
                [
                    f"Z {fmt(section['total_depth_h_mm'], 0)} x {fmt(section['flange_width_b_mm'], 0)} x {fmt(section['lip_depth_d_mm'], 0)} x {fmt(section['thickness_t_mm'], 2)} mm",
                    f"{fmt(optimal_section['weight_kg_m'], 3)} kg/m",
                    f"{optimal_section['governing_utilization']:.1%}",
                    optimal_status,
                ],
            ],
            [2.6 * inch, 1.2 * inch, 1.5 * inch, 2.0 * inch],
            "#336699",
        )
    else:
        story.append(
            Paragraph(
                "No optimal section recommendation was available for this run.",
                normal_style,
            )
        )

    story.append(Paragraph("9. References and conclusion", heading_style))
    conclusion = "PASS" if all_ok else "REVIEW REQUIRED"
    conclusion_text = (
        f"Overall conclusion for the submitted trial section: <b>{conclusion}</b>. "
        "A PASS indicates the trial section satisfies the simplified checks included in this preliminary scaffold. "
        "A REVIEW REQUIRED result means at least one geometry, strength, LTB, biaxial, deflection or connection check exceeds the permissible screening limit and should be revised or verified by detailed engineering analysis. "
        "References used: IS 801:1975 Clause 5.2 for element proportioning, IS 801:1975 Clause 5.2.1 for effective-width screening, IS 801:1975 bending and combined-stress guidance for stress and interaction screening, IS 875 Parts 1, 2 and 3 for service load inputs, and IS 1367 / IS 800 guidance for support fastener screening. "
        "This report is not a certified design package; final design must confirm code edition, section properties, local buckling, torsion, restraint, connections and project criteria."
    )
    story.append(Paragraph(conclusion_text, normal_style))
    story.append(
        Paragraph(
            f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            normal_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
