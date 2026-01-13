import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import json


def generate_pdf(report_path: str, meta: dict, assets: dict, original_image_path: str):
    doc = SimpleDocTemplate(report_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph('DroneAPP Plant Health Report', styles['Title'])
    story.append(title)
    story.append(Spacer(1, 6 * mm))

    info = f"Date: {datetime.utcnow().isoformat()}"
    story.append(Paragraph(info, styles['Normal']))
    story.append(Spacer(1, 4 * mm))

    # Original image
    story.append(Paragraph('Original image:', styles['Heading3']))
    story.append(Spacer(1, 2 * mm))
    try:
        story.append(RLImage(original_image_path, width=140 * mm, height=90 * mm))
    except Exception:
        story.append(Paragraph('Could not include original image.', styles['Normal']))
    story.append(Spacer(1, 4 * mm))

    # Assets
    story.append(Paragraph('Analysis maps:', styles['Heading3']))
    story.append(Spacer(1, 2 * mm))
    # Table of two images
    imgs = []
    try:
        imgs.append(RLImage(assets['heat_exg'], width=80 * mm, height=60 * mm))
    except Exception:
        imgs.append(Paragraph('ExG heatmap not available', styles['Normal']))
    try:
        imgs.append(RLImage(assets['heat_vari'], width=80 * mm, height=60 * mm))
    except Exception:
        imgs.append(Paragraph('VARI heatmap not available', styles['Normal']))

    t = Table([imgs], colWidths=[90 * mm, 90 * mm])
    story.append(t)
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph('Overlay:', styles['Heading3']))
    story.append(Spacer(1, 2 * mm))
    try:
        story.append(RLImage(assets['overlay'], width=140 * mm, height=90 * mm))
    except Exception:
        story.append(Paragraph('Overlay not available', styles['Normal']))
    story.append(Spacer(1, 6 * mm))

    # Metrics table
    story.append(Paragraph('Metrics:', styles['Heading3']))
    story.append(Spacer(1, 2 * mm))
    metrics = meta.get('metrics', {})
    table_data = [['Metric', 'Value']]
    for k, v in metrics.items():
        table_data.append([k, f"{v:.2f}" if isinstance(v, float) else str(v)])

    tbl = Table(table_data, colWidths=[90 * mm, 90 * mm])
    tbl.setStyle(
        TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ])
    )
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))

    # Conclusion
    story.append(Paragraph('Conclusion:', styles['Heading3']))
    if metrics.get('vegetation_coverage_percent', 0) < 5:
        story.append(Paragraph('Low vegetation coverage detected.', styles['Normal']))
    if metrics.get('vari_mean', 0) < 0.2:
        story.append(Paragraph('Low VARI mean — possible plant stress.', styles['Normal']))
    if metrics.get('health_score', 0) > 70:
        story.append(Paragraph('Overall good plant health detected.', styles['Normal']))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph('Note: NDVI requires multispectral data and will be added later.', styles['Italic']))

    doc.build(story)

    # Write meta to JSON next to pdf
    meta_path = os.path.splitext(report_path)[0] + '.json'
    with open(meta_path, 'w') as fh:
        json.dump(meta, fh)

    return report_path
