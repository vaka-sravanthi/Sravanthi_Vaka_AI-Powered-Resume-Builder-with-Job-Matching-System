import io
import base64
import os
import sys
from typing import Any, Dict, List, Tuple

def check_pdf_dependencies():
    """Check which PDF libraries are available and provide installation instructions"""
    print("=" * 60)
    print("PDF LIBRARY DIAGNOSTICS")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    weasyprint_available = False
    try:
        import weasyprint
        from weasyprint import HTML, CSS
        print("✅ WeasyPrint: AVAILABLE")
        print(f"   Version: {weasyprint.__version__}")
        weasyprint_available = True
    except ImportError as e:
        print("❌ WeasyPrint: NOT AVAILABLE")
        print(f"   Error: {e}")
        print("   Install with: pip install weasyprint")
        if sys.platform == "linux":
            print("   Linux users may need: sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0")
        elif sys.platform == "darwin": 
            print("   macOS users may need: brew install python3 cairo pango gdk-pixbuf libffi")
        elif sys.platform == "win32":
            print("   Windows users: WeasyPrint should work with just 'pip install weasyprint'")
    except Exception as e:
        print(f" WeasyPrint: ERROR - {e}")
    
    print()
    reportlab_available = False
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        print("ReportLab: AVAILABLE")
        reportlab_available = True
        
        try:
            import reportlab
            print(f"  Version: {reportlab.__version__}")
        except:
            print(" Version: Unknown")
            
    except ImportError as e:
        print(" ReportLab: NOT AVAILABLE")
        print(f"   Error: {e}")
        print("   Install with: pip install reportlab")
    except Exception as e:
        print(f" ReportLab: ERROR - {e}")
    
    print()
    print("=" * 60)
    
    if not weasyprint_available and not reportlab_available:
        print(" CRITICAL: No PDF libraries available!")
        print()
        print("QUICK FIX - Install ReportLab (easier option):")
        print("   pip install reportlab")
        print()
        print("OR install WeasyPrint (better formatting):")
        if sys.platform == "win32":
            print("   pip install weasyprint")
        elif sys.platform == "darwin":
            print("   brew install cairo pango gdk-pixbuf libffi")
            print("   pip install weasyprint")
        elif sys.platform == "linux":
            print("   sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0")
            print("   pip install weasyprint")
        
        return False, False
    
    return weasyprint_available, reportlab_available


def generate_pdf_report_safe(
    candidate_name: str,
    match_score: float,
    confidence: float,
    explanation: str,
    missing_skills: List[str],
    top_snippets: List[Tuple[str, float]],
) -> bytes:
    print("DEBUG: Starting PDF report generation...")
    has_weasyprint, has_reportlab = check_pdf_dependencies()
    if not has_weasyprint and not has_reportlab:
        raise ImportError("Neither WeasyPrint nor ReportLab is available. Please install one of them.")
    
    if has_weasyprint:
        print("DEBUG: Using WeasyPrint for PDF generation")
        try:
            from weasyprint import HTML, CSS
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='utf-8'>
                <title>Resume-Job Match Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    h1 {{ color: #2c3e50; }}
                    .score {{ color: #27ae60; font-size: 1.2em; font-weight: bold; }}
                    .section {{ margin: 20px 0; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Resume-Job Match Report</h1>
                </div>
                
                <div class="section">
                    <p><strong>Candidate:</strong> {candidate_name or 'Unknown'}</p>
                    <p><strong>Match Score:</strong> <span class="score">{match_score:.1f}%</span></p>
                    <p><strong>Confidence:</strong> {confidence:.2f}</p>
                </div>
                
                <div class="section">
                    <h2>Analysis</h2>
                    <p>{explanation}</p>
                </div>
                
                {f"<div class='section'><h2>Missing Skills</h2><p>{', '.join(missing_skills)}</p></div>" if missing_skills else ""}
                
                {"<div class='section'><h2>Top Matching Snippets</h2>" if top_snippets else ""}
                {f"<table><tr><th>Text</th><th>Score</th></tr>{''.join([f'<tr><td>{text[:100]}...</td><td>{score:.2f}</td></tr>' for text, score in top_snippets[:5]])}</table></div>" if top_snippets else ""}
            </body>
            </html>
            """
            
            buf = io.BytesIO()
            HTML(string=html).write_pdf(target=buf)
            print("DEBUG: WeasyPrint PDF generated successfully")
            return buf.getvalue()
            
        except Exception as e:
            print(f"DEBUG: WeasyPrint failed: {e}")
            if not has_reportlab:
                raise e
            print("DEBUG: Falling back to ReportLab")
    
    if has_reportlab:
        print("DEBUG: Using ReportLab for PDF generation")
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import inch
            
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            elements.append(Paragraph("Resume-Job Match Report", styles["Title"]))
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph(f"<b>Candidate:</b> {candidate_name or 'Unknown'}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Match Score:</b> {match_score:.1f}%", styles["Normal"]))
            elements.append(Paragraph(f"<b>Confidence:</b> {confidence:.2f}", styles["Normal"]))
            elements.append(Spacer(1, 12))
            
            elements.append(Paragraph("Analysis", styles["Heading2"]))
            elements.append(Paragraph(explanation, styles["Normal"]))
            elements.append(Spacer(1, 12))
            
            if missing_skills:
                elements.append(Paragraph("Missing Skills", styles["Heading2"]))
                elements.append(Paragraph(", ".join(missing_skills), styles["Normal"]))
                elements.append(Spacer(1, 12))
            
            if top_snippets:
                elements.append(Paragraph("Top Matching Snippets", styles["Heading2"]))
                data = [["Text", "Score"]]
                for text, score in top_snippets[:5]:
                    data.append([text[:60] + "..." if len(text) > 60 else text, f"{score:.2f}"])
                
                table = Table(data, colWidths=[4*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
            
            doc.build(elements)
            print("DEBUG: ReportLab PDF generated successfully")
            return buf.getvalue()
            
        except Exception as e:
            print(f"DEBUG: ReportLab failed: {e}")
            raise e
    
    raise Exception("No PDF library available")


def _generate_experience_html(experiences):
    """Helper to generate experience HTML"""
    if not experiences:
        return ""
    
    html = '<div class="section"><div class="section-title">Professional Experience</div>'
    
    for exp in experiences:
        if isinstance(exp, dict):
            title = exp.get("title", "")
            company = exp.get("company", "")
            dates = f"{exp.get('start', '')} - {exp.get('end', '')}"
            
            html += f'<div class="experience-item">'
            html += f'<div class="job-title">{title} at {company}</div>'
            html += f'<div class="job-details">{dates}</div>'
            
            bullets = exp.get("bullets", [])
            if bullets:
                html += '<ul>'
                for bullet in bullets:
                    html += f'<li>{bullet}</li>'
                html += '</ul>'
            html += '</div>'
    
    html += '</div>'
    return html


def _generate_education_html(educations):
    """Helper to generate education HTML"""
    if not educations:
        return ""
    
    html = '<div class="section"><div class="section-title">Education</div>'
    
    for edu in educations:
        if isinstance(edu, dict):
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            year = edu.get("year", "")
            
            html += f'<div class="experience-item">'
            html += f'<div class="job-title">{degree}</div>'
            html += f'<div class="job-details">{school} - {year}</div>'
            html += '</div>'
    
    html += '</div>'
    return html


def generate_ats_resume_pdf_safe(data: Dict[str, Any]) -> bytes:
    print("DEBUG: Starting ATS resume PDF generation...")
    
    has_weasyprint, has_reportlab = check_pdf_dependencies()
    
    if not has_weasyprint and not has_reportlab:
        raise ImportError("Neither WeasyPrint nor ReportLab is available. Please install one of them.")
    
    name = str(data.get("name", "Your Name")).strip()
    email = str(data.get("email", "")).strip()
    phone = str(data.get("phone", "")).strip()
    location = str(data.get("location", "")).strip()
    summary = str(data.get("summary", "")).strip()
    
    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)  
    if location:
        contact_parts.append(location)
    
    for field in ["linkedin", "github", "portfolio", "website"]:
        link = str(data.get(field, "")).strip()
        if link:
            if not link.startswith(('http://', 'https://')):
                if field in ["linkedin", "github"]:
                    link = f"https://{field}.com/{'in/' if field == 'linkedin' else ''}{link}"
                else:
                    link = f"https://{link}"
            contact_parts.append(link)
    
    contact_line = " | ".join(contact_parts)
    print(f"DEBUG: Contact line: {contact_line}")
    
    if has_weasyprint:
        print("DEBUG: Using WeasyPrint for resume generation")
        try:
            from weasyprint import HTML, CSS
            
            exp_html = _generate_experience_html(data.get("experience", []))
            edu_html = _generate_education_html(data.get("education", []))
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='utf-8'>
                <title>ATS Resume - {name}</title>
                <style>
                    body {{ font-family: Calibri, Arial, sans-serif; margin: 20px; color: #333; }}
                    .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0066cc; padding-bottom: 15px; }}
                    .name {{ font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 10px; }}
                    .contact {{ font-size: 12px; color: #666; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ font-size: 16px; font-weight: bold; color: #0066cc; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-bottom: 10px; }}
                    .experience-item {{ margin-bottom: 15px; }}
                    .job-title {{ font-weight: bold; color: #333; }}
                    .job-details {{ color: #666; font-size: 11px; margin-bottom: 5px; }}
                    ul {{ margin: 5px 0; padding-left: 20px; }}
                    li {{ margin-bottom: 3px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="name">{name}</div>
                    <div class="contact">{contact_line}</div>
                </div>
                
                {f'<div class="section"><div class="section-title">Professional Summary</div><p>{summary}</p></div>' if summary else ''}
                
                <div class="section">
                    <div class="section-title">Skills</div>
                    <p>{", ".join([str(s) for s in data.get("skills", [])])}</p>
                </div>
                
                {exp_html}
                {edu_html}
            </body>
            </html>
            """
            
            buf = io.BytesIO()
            HTML(string=html).write_pdf(target=buf)
            print("DEBUG: WeasyPrint resume PDF generated successfully")
            return buf.getvalue()
            
        except Exception as e:
            print(f"DEBUG: WeasyPrint failed: {e}")
            if not has_reportlab:
                raise e
    
    if has_reportlab:
        print("DEBUG: Using ReportLab for resume generation")
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            elements.append(Paragraph(name, styles["Title"]))
            elements.append(Paragraph(contact_line, styles["Normal"]))
            elements.append(Spacer(1, 12))
            
            if summary:
                elements.append(Paragraph("PROFESSIONAL SUMMARY", styles["Heading2"]))
                elements.append(Paragraph(summary, styles["Normal"]))
                elements.append(Spacer(1, 12))
            
            skills = data.get("skills", [])
            if skills:
                elements.append(Paragraph("SKILLS", styles["Heading2"]))
                elements.append(Paragraph(", ".join([str(s) for s in skills]), styles["Normal"]))
                elements.append(Spacer(1, 12))
            
            experiences = data.get("experience", [])
            if experiences:
                elements.append(Paragraph("EXPERIENCE", styles["Heading2"]))
                for exp in experiences:
                    if isinstance(exp, dict):
                        title = f"{exp.get('title', '')} at {exp.get('company', '')}"
                        elements.append(Paragraph(title, styles["Heading3"]))
                        
                        bullets = exp.get("bullets", [])
                        for bullet in bullets:
                            elements.append(Paragraph(f"• {bullet}", styles["Normal"]))
                        elements.append(Spacer(1, 8))
            
            doc.build(elements)
            print("DEBUG: ReportLab resume PDF generated successfully")
            return buf.getvalue()
            
        except Exception as e:
            print(f"DEBUG: ReportLab failed: {e}")
            raise e
    
    raise Exception("No PDF library available")


def test_installation():
    """Test the installation and generate sample PDFs"""
    print("TESTING PDF GENERATION INSTALLATION")
    print("=" * 50)
    
    has_weasyprint, has_reportlab = check_pdf_dependencies()
    
    if not has_weasyprint and not has_reportlab:
        print("\n🚨 Cannot proceed - no PDF libraries available!")
        print("Please install at least one PDF library and try again.")
        return
    
    print("\n📋 Testing Report Generation...")
    try:
        report_pdf = generate_pdf_report_safe(
            candidate_name="Test User",
            match_score=85.0,
            confidence=0.9,
            explanation="This is a test report to verify PDF generation is working.",
            missing_skills=["Python", "Machine Learning"],
            top_snippets=[("Sample text snippet", 0.85), ("Another snippet", 0.78)]
        )
        print(f"✅ Report PDF generated: {len(report_pdf)} bytes")
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
    
    print("\n📄 Testing Resume Generation...")
    try:
        sample_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "123-456-7890",
            "location": "San Francisco, CA",
            "linkedin": "testuser",
            "github": "testuser",
            "summary": "Test summary for resume generation.",
            "skills": ["Python", "JavaScript", "React"],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Test Company",
                    "start": "2020",
                    "end": "2023",
                    "bullets": ["Developed applications", "Led projects"]
                }
            ]
        }
        
        resume_pdf = generate_ats_resume_pdf_safe(sample_data)
        print(f"✅ Resume PDF generated: {len(resume_pdf)} bytes")
    except Exception as e:
        print(f"❌ Resume generation failed: {e}")
    
    print("\n🎉 Installation test complete!")


if __name__ == "__main__":
    test_installation()