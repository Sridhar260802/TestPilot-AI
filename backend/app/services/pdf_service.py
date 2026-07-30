from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_report(data, filename="website_report.pdf"):

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>TestPilot AI - Website Report</b>", styles["Title"]))
    story.append(Paragraph("<br/>", styles["Normal"]))

    for key, value in data.items():
        story.append(
            Paragraph(f"<b>{key}</b>: {value}", styles["Normal"])
        )

    doc.build(story)

    return filename