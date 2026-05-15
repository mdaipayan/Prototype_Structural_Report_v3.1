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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
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
    web = patches.Rectangle((t, t), t, h - 2*t, linewidth=2, 
                             edgecolor='darkblue', facecolor='lightblue', alpha=0.7)
    ax.add_patch(web)
    
    # Top flange
    top_flange = patches.Rectangle((0, h - t), b, t, linewidth=2, 
                                    edgecolor='darkblue', facecolor='lightblue', alpha=0.7)
    ax.add_patch(top_flange)
    
    # Bottom flange
    bottom_flange = patches.Rectangle((0, 0), b, t, linewidth=2, 
                                       edgecolor='darkblue', facecolor='lightblue', alpha=0.7)
    ax.add_patch(bottom_flange)
    
    # Top lip
    top_lip = patches.Rectangle((b - t, h - t - d), t, d, linewidth=2, 
                                 edgecolor='darkblue', facecolor='lightblue', alpha=0.7)
    ax.add_patch(top_lip)
    
    # Bottom lip
    bottom_lip = patches.Rectangle((b - t, t), t, d, linewidth=2, 
                                    edgecolor='darkblue', facecolor='lightblue', alpha=0.7)
    ax.add_patch(bottom_lip)
    
    # Add dimensions with arrows
    ax.annotate('', xy=(b + 0.3, 0), xytext=(b + 0.3, h),
                arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
    ax.text(b + 0.5, h/2, f'h={total_depth_h_mm}mm', fontsize=9, color='red', 
            rotation=90, va='center')
    
    ax.annotate('', xy=(0, -0.4), xytext=(b, -0.4),
                arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
    ax.text(b/2, -0.6, f'b={flange_width_b_mm}mm', fontsize=9, color='red', ha='center')
    
    ax.annotate('', xy=(b + 0.15, h - t), xytext=(b + 0.15, h - t - d),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
    ax.text(b + 0.35, h - t - d/2, f'd={lip_depth_d_mm}mm', fontsize=8, color='green', 
            rotation=90, va='center')
    
    ax.text(t/2, h/2, f't={thickness_t_mm}mm', fontsize=7, color='black', 
            ha='center', va='center', weight='bold')
    
    ax.set_xlim(-0.2, b + 1.0)
    ax.set_ylim(-0.8, h + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Z-Section Profile', fontsize=12, weight='bold', pad=10)
    
    plt.tight_layout()
    
    # Save to BytesIO
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close(fig)
    
    return Image(img_buffer, width=2.5*inch, height=3.0*inch)


def create_design_report(
    inputs: Dict[str, Any],
    flat_width_checks: Dict[str, Any],
    resolved_loads: Dict[str, Any],
    design_moments: Dict[str, Any],
    project_name: str = "Z-Purlin Design",
    location: str = "Project Location",
    designer: str = "Structural Designer",
) -> bytes:
    """Create a production-ready PDF report for Z-purlin design.
    
    Args:
        inputs: ZPurlinASDInputs as dictionary
        flat_width_checks: Results from z_purlin_flat_width_checks()
        resolved_loads: Results from z_purlin_resolved_loads()
        design_moments: Results from z_purlin_design_moments()
        project_name: Project identification
        location: Project location
        designer: Designer name
    
    Returns:
        PDF bytes ready for download
    """
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#003366'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=HexColor('#003366'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        textColor=black,
        spaceAfter=4
    )
    
    # Title and project info
    story.append(Paragraph("Z-PURLIN DESIGN REPORT", title_style))
    story.append(Paragraph("IS 801:1975 Allowable Stress Design (ASD)", styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Project header table
    project_data = [
        ['Project:', project_name, 'Date:', datetime.now().strftime('%Y-%m-%d')],
        ['Location:', location, 'Designer:', designer],
        ['Standard:', 'IS 801:1975 ASD', 'Code Version:', '1975'],
    ]
    
    project_table = Table(project_data, colWidths=[1.2*inch, 2.0*inch, 1.2*inch, 2.0*inch])
    project_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#E8F4F8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), TA_LEFT),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#999999')),
    ]))
    story.append(project_table)
    story.append(Spacer(1, 15))
    
    # SECTION 1: Design Inputs
    story.append(Paragraph("1. DESIGN INPUTS", heading_style))
    
    inputs_data = [
        ['Parameter', 'Value', 'Unit'],
        ['Material Yield Strength (Fy)', f"{inputs['fy_mpa']:.1f}", 'MPa'],
        ['Purlin Span', f"{inputs['span_m']:.2f}", 'm'],
        ['Purlin Spacing', f"{inputs['spacing_m']:.3f}", 'm'],
        ['Roof Slope', f"{inputs['slope_deg']:.1f}", '°'],
        ['Dead Load', f"{inputs['dead_load_kn_m2']:.3f}", 'kN/m²'],
        ['Live Load', f"{inputs['live_load_kn_m2']:.3f}", 'kN/m²'],
        ['Wind Load', f"{inputs['wind_load_kn_m2']:.3f}", 'kN/m²'],
    ]
    
    inputs_table = Table(inputs_data, colWidths=[3.0*inch, 1.5*inch, 1.0*inch])
    inputs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), TA_CENTER),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F5F5F5')]),
    ]))
    story.append(inputs_table)
    story.append(Spacer(1, 12))
    
    # Z-Section dimensions
    section_data = [
        ['Parameter', 'Value', 'Unit'],
        ['Total Depth (h)', f"{inputs['total_depth_h_mm']:.1f}", 'mm'],
        ['Flange Width (b)', f"{inputs['flange_width_b_mm']:.1f}", 'mm'],
        ['Lip Depth (d)', f"{inputs['lip_depth_d_mm']:.1f}", 'mm'],
        ['Thickness (t)', f"{inputs['thickness_t_mm']:.2f}", 'mm'],
    ]
    
    section_table = Table(section_data, colWidths=[3.0*inch, 1.5*inch, 1.0*inch])
    section_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#336699')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), TA_CENTER),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F5F5F5')]),
    ]))
    story.append(section_table)
    story.append(Spacer(1, 12))
    
    # Z-section diagram
    story.append(Paragraph("Z-Section Profile:", styles['Normal']))
    try:
        diagram = generate_z_section_diagram(
            inputs['total_depth_h_mm'],
            inputs['flange_width_b_mm'],
            inputs['lip_depth_d_mm'],
            inputs['thickness_t_mm']
        )
        story.append(diagram)
    except Exception as e:
        story.append(Paragraph(f"[Diagram generation unavailable: {str(e)}]", 
                              ParagraphStyle('Error', parent=styles['Normal'], 
                                            textColor=HexColor('#CC0000'))))
    
    story.append(Spacer(1, 12))
    
    # SECTION 2: Preliminary Checks
    story.append(Paragraph("2. PRELIMINARY CHECKS (IS 801:1975 Clause 5.2)", heading_style))
    story.append(Spacer(1, 6))
    
    web_status = "✓ PASS" if flat_width_checks['web_ratio_ok'] else "✗ FAIL"
    flange_status = "✓ PASS" if flat_width_checks['flange_ratio_ok'] else "✗ FAIL"
    
    checks_data = [
        ['Check', 'Actual', 'Limit', 'Status'],
        ['Web h/t ratio', f"{flat_width_checks['web_ratio']:.1f}", 
         f"{flat_width_checks['web_ratio_limit']:.1f}", web_status],
        ['Flange b/t ratio', f"{flat_width_checks['flange_ratio']:.1f}", 
         f"{flat_width_checks['flange_ratio_limit']:.1f}", flange_status],
    ]
    
    checks_table = Table(checks_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.0*inch])
    checks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#660033')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), TA_CENTER),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
         [HexColor('#E8F8E8') if flat_width_checks['web_ratio_ok'] else HexColor('#F8E8E8'),
          HexColor('#E8F8E8') if flat_width_checks['flange_ratio_ok'] else HexColor('#F8E8E8')]),
        ('TEXTCOLOR', (3, 1), (3, 2), HexColor('#006600') if flat_width_checks['web_ratio_ok'] else HexColor('#CC0000')),
        ('FONTNAME', (3, 1), (3, 2), 'Helvetica-Bold'),
    ]))
    story.append(checks_table)
    story.append(Spacer(1, 12))
    
    # SECTION 3: Resolved Line Loads
    story.append(Paragraph("3. RESOLVED LINE LOADS ON SLOPED ROOF", heading_style))
    
    loads_data = [
        ['Load Component', 'Gravity (kN/m)', 'Uplift (kN/m)'],
        ['Dead Load (line)', f"{resolved_loads['dead_line_load_kn_m']:.4f}", 
         f"{resolved_loads['dead_line_load_kn_m']:.4f}"],
        ['Live Load (line)', f"{resolved_loads['live_line_load_kn_m']:.4f}", '-'],
        ['Wind Load (line)', '-', f"{resolved_loads['wind_line_load_kn_m']:.4f}"],
        ['Total Line Load', f"{resolved_loads['gravity_line_load_kn_m']:.4f}", 
         f"{resolved_loads['uplift_line_load_kn_m']:.4f}"],
        ['Normal Component', f"{resolved_loads['gravity_normal_kn_m']:.4f}", 
         f"{resolved_loads['uplift_normal_kn_m']:.4f}"],
        ['Tangential Component', f"{resolved_loads['gravity_tangential_kn_m']:.4f}", 
         f"{resolved_loads['uplift_tangential_kn_m']:.4f}"],
    ]
    
    loads_table = Table(loads_data, colWidths=[3.0*inch, 2.0*inch, 2.0*inch])
    loads_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), TA_CENTER),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F5F5F5')]),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
    ]))
    story.append(loads_table)
    story.append(Spacer(1, 12))
    
    # SECTION 4: Design Moments
    story.append(Paragraph("4. DESIGN MOMENTS (Continuous Span, WL²/n)", heading_style))
    
    moments_data = [
        ['Loading Case', 'Axis', 'Moment (kN-m)'],
        ['Gravity (DL+LL)', 'Major (Normal)', f"{design_moments['gravity_major_axis_kn_m']:.4f}"],
        ['Gravity (DL+LL)', 'Minor (Tangential)', f"{design_moments['gravity_minor_axis_kn_m']:.4f}"],
        ['Uplift (DL+WL)', 'Major (Normal)', f"{design_moments['uplift_major_axis_kn_m']:.4f}"],
    ]
    
    moments_table = Table(moments_data, colWidths=[2.5*inch, 2.0*inch, 2.5*inch])
    moments_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), TA_CENTER),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F5F5F5')]),
    ]))
    story.append(moments_table)
    story.append(Spacer(1, 15))
    
    # Disclaimers and notes
    story.append(PageBreak())
    story.append(Paragraph("DESIGN NOTES & DISCLAIMERS", heading_style))
    story.append(Spacer(1, 8))
    
    disclaimer_text = """
    <b>Scope of Calculations:</b><br/>
    This report covers preliminary screening calculations for Z-purlin design 
    per IS 801:1975 Allowable Stress Design (ASD) framework.<br/>
    <br/>
    <b>Included Checks:</b><br/>
    • Flat-width ratio verification (Clause 5.2)<br/>
    • Load resolution on sloped roofs<br/>
    • Preliminary moment calculations (continuous span, simplified)<br/>
    <br/>
    <b>NOT Included (Manual Verification Required):</b><br/>
    • Effective-width reduction analysis<br/>
    • Lateral-torsional buckling (LTB) checks<br/>
    • Biaxial bending interaction<br/>
    • Deflection limits<br/>
    • Connection design<br/>
    • Torsional stresses<br/>
    <br/>
    <b>Important Limitations:</b><br/>
    • This calculation is for preliminary design screening only<br/>
    • Final design must be verified by a qualified structural engineer<br/>
    • Section properties should be confirmed from manufacturer tables or cold-formed 
    software<br/>
    • Local building codes and project-specific criteria take precedence<br/>
    • Ensure all assumptions are appropriate for the specific project<br/>
    <br/>
    <b>Next Steps for Final Design:</b><br/>
    1. Perform effective-width analysis per IS 801:1975<br/>
    2. Calculate actual section properties (use CalcProp, CFS, or similar)<br/>
    3. Check lateral-torsional buckling (LTB) limits<br/>
    4. Verify biaxial bending interaction ratios<br/>
    5. Check deflection against L/limit (typically L/180 or L/240)<br/>
    6. Design and detail connections<br/>
    7. Prepare final engineering drawings and specifications<br/>
    <br/>
    <b>Report Generated:</b> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
    """
    
    story.append(Paragraph(disclaimer_text, normal_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
