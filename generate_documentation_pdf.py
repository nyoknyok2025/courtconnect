from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors

TITLE = 'CourtConnect: Corruption Reporting System'
AUTHOR = 'Student Name'
COURSE = 'Software Engineering / Information Systems'
SECTION = 'Section A'

content = []
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleStyle', parent=styles['Title'], fontName='Times-Bold', fontSize=20, leading=24, alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name='SubtitleStyle', parent=styles['Heading2'], fontName='Times-Roman', fontSize=12, leading=16, alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name='BodyStyle', parent=styles['BodyText'], fontName='Times-Roman', fontSize=12, leading=16, alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name='HeadingStyle', parent=styles['Heading2'], fontName='Times-Bold', fontSize=14, leading=18, spaceBefore=12, spaceAfter=8))
styles.add(ParagraphStyle(name='CaptionStyle', parent=styles['BodyText'], fontName='Times-Italic', fontSize=10, leading=12, alignment=TA_CENTER, textColor=colors.grey))

content.append(Paragraph(TITLE, styles['TitleStyle']))
content.append(Paragraph(f'Prepared by: {AUTHOR}', styles['SubtitleStyle']))
content.append(Paragraph(f'Course: {COURSE}', styles['SubtitleStyle']))
content.append(Paragraph(f'Section: {SECTION}', styles['SubtitleStyle']))
content.append(Spacer(1, 0.5 * inch))

content.append(Paragraph('Introduction', styles['HeadingStyle']))
content.append(Paragraph(
    'CourtConnect is a web-based corruption reporting system designed to help citizens report misconduct, unsafe public services, bribery, and governance issues in a secure and organized manner. The system allows users to submit reports, track their status, and interact with administrative dashboards. It also includes a machine learning component that predicts the category of a report based on the description entered by the reporter.',
    styles['BodyStyle']
))

content.append(Paragraph('System Modules', styles['HeadingStyle']))
modules = [
    'User Authentication Module: Handles login, registration, and user access control.',
    'Report Submission Module: Enables users to create reports with title, description, category, severity, location, and evidence files.',
    'Report Management Module: Allows administrators to review, update, and manage report statuses and comments.',
    'Dashboard Module: Provides separate dashboards for regular users and administrators to monitor reports and performance.',
    'Machine Learning Module: Uses a trained classifier to predict the category of a report based on its description.',
    'API Module: Exposes report data and prediction endpoints for integration or testing.',
]
content.append(ListFlowable([ListItem(Paragraph(item, styles['BodyStyle']), bulletColor=colors.black) for item in modules], bulletType='bullet', start='bullet'))

content.append(PageBreak())
content.append(Paragraph('System Screenshots and Explanation', styles['HeadingStyle']))
content.append(Paragraph('The system includes several key interfaces that support the reporting workflow.', styles['BodyStyle']))
content.append(Paragraph('1. Login Page', styles['BodyStyle']))
content.append(Paragraph('The login page allows registered users to securely access the application. It includes authentication controls and a visible captcha confirmation to reduce automated access.', styles['BodyStyle']))
content.append(Paragraph('2. Report Form', styles['BodyStyle']))
content.append(Paragraph('The report submission form collects details such as report title, description, category, severity, location, department, and evidence file, ensuring complete reporting.', styles['BodyStyle']))
content.append(Paragraph('3. Dashboard', styles['BodyStyle']))
content.append(Paragraph('The dashboard presents important information such as the number of reports created, resolved, and still pending, with different views for users and administrators.', styles['BodyStyle']))
content.append(Paragraph('4. Report Detail Page', styles['BodyStyle']))
content.append(Paragraph('The detail page shows report information and allows comments or updates to be added, making the reporting process transparent and trackable.', styles['BodyStyle']))

content.append(Paragraph('Real-World Application', styles['HeadingStyle']))
content.append(Paragraph(
    'CourtConnect can be applied in government agencies, public service offices, and civic organizations to make reporting misconduct easier and more transparent. It gives citizens a reliable digital method to report corruption and unsafe practices while enabling authorities to process and track complaints more efficiently.',
    styles['BodyStyle']
))

content.append(Paragraph('Conclusion', styles['HeadingStyle']))
content.append(Paragraph(
    'In conclusion, CourtConnect provides an effective and practical solution for managing corruption reports. Its combination of user-friendly interfaces, administrative tools, and machine learning support makes it a valuable system for improving accountability and public service transparency.',
    styles['BodyStyle']
))

filename = 'CourtConnect_Documentation.pdf'
doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
doc.build(content)
print(f'Created {filename}')
