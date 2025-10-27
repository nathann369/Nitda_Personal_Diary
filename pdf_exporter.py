from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def export_entry_to_pdf(entry, filename=None):
    if not filename:
        safe = entry.title.strip().replace(' ', '_') or 'entry'
        filename = f"{safe}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>{entry.title}</b>", styles['Title']),
        Spacer(1,12),
        Paragraph(f"<i>Date:</i> {entry.date}", styles['Normal']),
        Spacer(1,12),
        Paragraph(entry.content.replace('\n','<br/>'), styles['BodyText']),
    ]
    doc.build(story)
    return filename
