from __future__ import annotations

import io
import base64
import os
from typing import Any, Dict, List, Tuple

try:
    from weasyprint import HTML, CSS
    _HAS_WEASYPRINT = True
except Exception:
    HTML = None
    CSS = None
    _HAS_WEASYPRINT = False


def generate_pdf_report(
    candidate_name: str,
    match_score: float,
    confidence: float,
    explanation: str,
    missing_skills: List[str],
    top_snippets: List[Tuple[str, float]],
) -> bytes:
    print("DEBUG: Generating PDF report...")
    print(f"DEBUG: Candidate: {candidate_name}, Score: {match_score}, Confidence: {confidence}")
    
    if _HAS_WEASYPRINT:
        html_snippets = ""
        if top_snippets:
            snippet_rows = []
            for text, sim in (top_snippets or [])[:5]:
                truncated_text = text[:120] + ('...' if len(text) > 120 else '')
                truncated_text = (truncated_text
                                .replace('&', '&amp;')
                                .replace('<', '&lt;')
                                .replace('>', '&gt;')
                                .replace('"', '&quot;'))
                snippet_rows.append(
                    f"<tr><td>{truncated_text}</td><td style='text-align:center'>{sim:.2f}</td></tr>"
                )
            html_snippets = "".join(snippet_rows)
        
        html_missing = ""
        if missing_skills:
            escaped_skills = [skill.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') 
                            for skill in missing_skills]
            html_missing = ", ".join(escaped_skills)
        
        safe_explanation = (explanation
                          .replace('&', '&amp;')
                          .replace('<', '&lt;')
                          .replace('>', '&gt;')
                          .replace('\n', '<br>'))
        
        safe_candidate_name = (candidate_name or 'Unknown').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        html = f"""
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset='utf-8' />
            <title>Resume-Job Match Report</title>
            <style>
              body {{ 
                font-family: 'Segoe UI', 'Arial', sans-serif; 
                margin: 24px; 
                color: #333; 
                line-height: 1.6;
                background: white;
              }}
              
              .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 3px solid #3498db;
              }}
              
              h1 {{ 
                margin: 0 0 8px; 
                color: #2c3e50; 
                font-size: 28pt;
                font-weight: bold;
              }}
              
              .report-meta {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 25px;
                border-left: 5px solid #3498db;
              }}
              
              .report-meta p {{ 
                margin: 8px 0; 
                font-size: 12pt;
              }}
              
              .score-highlight {{
                color: #27ae60;
                font-size: 1.3em;
                font-weight: bold;
              }}
              
              .confidence-highlight {{
                color: #e67e22;
                font-weight: bold;
              }}
              
              h2 {{ 
                margin: 25px 0 12px; 
                color: #34495e; 
                border-bottom: 2px solid #3498db; 
                padding-bottom: 8px; 
                font-size: 16pt;
              }}
              
              .explanation {{
                background: #ffffff;
                padding: 20px;
                border-radius: 6px;
                border: 1px solid #e1e8ed;
                margin-bottom: 20px;
                font-size: 11pt;
                line-height: 1.7;
              }}
              
              .missing-skills {{
                background: #fdf2f2;
                padding: 15px;
                border-radius: 6px;
                border-left: 4px solid #e74c3c;
                color: #c0392b;
                font-weight: 500;
                margin-bottom: 20px;
              }}
              
              table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin: 15px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
              }}
              
              th, td {{ 
                border: 1px solid #ddd; 
                padding: 12px 10px; 
                text-align: left;
              }}
              
              th {{ 
                background: #34495e; 
                color: white;
                text-align: left; 
                font-weight: 600; 
                font-size: 11pt;
              }}
              
              td {{
                background: white;
                font-size: 10pt;
              }}
              
              tr:nth-child(even) td {{
                background: #f9f9f9;
              }}
              
              .similarity-score {{
                font-weight: bold;
                color: #2980b9;
              }}
              
              .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #bdc3c7;
                text-align: center;
                color: #7f8c8d;
                font-size: 9pt;
              }}
              
              @page {{
                size: A4;
                margin: 0.75in;
              }}
              
              @media print {{
                .header {{
                  break-after: avoid;
                }}
                
                .report-meta, .explanation {{
                  break-inside: avoid;
                }}
                
                table {{
                  break-inside: avoid;
                }}
              }}
            </style>
          </head>
          <body>
            <div class="header">
              <h1>Resume–Job Match Report</h1>
            </div>
            
            <div class='report-meta'>
              <p><strong>Candidate:</strong> {safe_candidate_name}</p>
              <p><strong>Match Score:</strong> <span class='score-highlight'>{match_score:.1f}%</span></p>
              <p><strong>Confidence Level:</strong> <span class='confidence-highlight'>{confidence:.2f}</span></p>
              <p><strong>Report Generated:</strong> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>Match Analysis</h2>
            <div class='explanation'>{safe_explanation}</div>
            
            {f"<h2>Skills Gap Analysis</h2><div class='missing-skills'><strong>Missing Skills:</strong> {html_missing}</div>" if html_missing else ''}
            
            {"<h2>Top Matching Resume Snippets</h2>" if html_snippets else ""}
            {f"<table><thead><tr><th style='width: 70%'>Resume Content</th><th style='width: 30%'>Similarity Score</th></tr></thead><tbody>{html_snippets}</tbody></table>" if html_snippets else ""}
            
            <div class="footer">
              <p>This report was generated automatically by the AI Resume Matching System.</p>
            </div>
          </body>
        </html>
        """
        
        buf = io.BytesIO()
        try:
            HTML(string=html).write_pdf(
                target=buf, 
                stylesheets=[CSS(string="@page { size: A4; margin: 0.75in; }")]
            )
            print("DEBUG: PDF report generated successfully with WeasyPrint")
            return buf.getvalue()
        except Exception as e:
            print(f"DEBUG: WeasyPrint error in report generation: {e}")
    
    print("DEBUG: Using ReportLab fallback for report generation")
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import inch
    except ImportError as e:
        print(f"DEBUG: ReportLab import error: {e}")
        raise ImportError("Neither WeasyPrint nor ReportLab is available for PDF generation")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=0.75*inch)
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontSize=20,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.Color(44/255, 62/255, 80/255)
    ))

    elements: List[Any] = []
    
    elements.append(Paragraph("Resume–Job Match Report", styles["ReportTitle"]))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph(f"<b>Candidate:</b> {candidate_name or 'Unknown'}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Match Score:</b> {match_score:.1f}%", styles["Normal"]))
    elements.append(Paragraph(f"<b>Confidence:</b> {confidence:.2f}", styles["Normal"]))
    elements.append(Spacer(1, 16))
    
    elements.append(Paragraph("Match Analysis", styles["Heading2"]))
    elements.append(Paragraph(explanation, styles["BodyText"]))
    elements.append(Spacer(1, 12))
    
    if missing_skills:
        elements.append(Paragraph("Skills Gap Analysis", styles["Heading2"]))
        elements.append(Paragraph(f"<b>Missing Skills:</b> {', '.join(missing_skills)}", styles["BodyText"]))
        elements.append(Spacer(1, 12))
    
    if top_snippets:
        elements.append(Paragraph("Top Matching Resume Snippets", styles["Heading2"]))
        data = [["Resume Content", "Similarity"]]
        for text, sim in top_snippets[:5]:
            truncated = text[:80] + ("..." if len(text) > 80 else "")
            data.append([truncated, f"{sim:.2f}"])
        
        table = Table(data, colWidths=[4*inch, 1*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(52/255, 73/255, 94/255)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(248/255, 249/255, 250/255)]),
        ]))
        elements.append(table)

    doc.build(elements)
    print("DEBUG: PDF report generated successfully with ReportLab")
    return buf.getvalue()


def generate_ats_resume_pdf(data: Dict[str, Any]) -> bytes:
    print("DEBUG: Starting ATS resume PDF generation...")
    print(f"DEBUG: Input data keys: {list(data.keys())}")
    
    if _HAS_WEASYPRINT:
        def join_nonempty(parts: List[str], sep: str = " · ") -> str:
            clean_parts = [str(p).strip() for p in parts if p and str(p).strip()]
            result = sep.join(clean_parts)
            print(f"DEBUG: join_nonempty({parts}) = '{result}'")
            return result

        def safe_get_string(key: str, default: str = "") -> str:
            try:
                value = data.get(key, default)
                if value is None:
                    result = ""
                else:
                    result = str(value).strip()
                print(f"DEBUG: {key} = '{result}'")
                return result
            except Exception as e:
                print(f"DEBUG: Error getting {key}: {e}")
                return ""

        def safe_get_list(key: str, default: List[str] = None) -> List[str]:
            if default is None:
                default = []
            try:
                value = data.get(key, default)
                if isinstance(value, list):
                    result = [str(item).strip() for item in value if item and str(item).strip()]
                elif isinstance(value, str) and value.strip():
                    result = [value.strip()]
                else:
                    result = []
                print(f"DEBUG: {key} list = {result}")
                return result
            except Exception as e:
                print(f"DEBUG: Error getting {key} list: {e}")
                return []

        name = safe_get_string("name")
        email = safe_get_string("email")
        phone = safe_get_string("phone")
        location = safe_get_string("location")
        
        if not name:
            print("WARNING: No name provided - using placeholder")
            name = "Your Name Here"

        print(f"DEBUG: Personal info - Name: '{name}', Email: '{email}', Phone: '{phone}', Location: '{location}'")

        contact_parts = []
        
        if email and email.strip():
            email_clean = email.strip()
            print(f"DEBUG: Adding email: {email_clean}")
            contact_parts.append(f'<a href="mailto:{email_clean}" class="contact-link">{email_clean}</a>')
        
        if phone and phone.strip():
            phone_clean = phone.strip()
            print(f"DEBUG: Adding phone: {phone_clean}")
            contact_parts.append(f'<span class="contact-item">{phone_clean}</span>')
        
        if location and location.strip():
            location_clean = location.strip()
            print(f"DEBUG: Adding location: {location_clean}")
            contact_parts.append(f'<span class="contact-item">{location_clean}</span>')

        print(f"DEBUG: Basic contact parts so far: {contact_parts}")

        def process_link(link_value: str, platform: str = "") -> str:
            if not link_value or not str(link_value).strip():
                return ""
            
            link = str(link_value).strip()
            print(f"DEBUG: Processing {platform} link: '{link}'")
            
            if link.startswith(('http://', 'https://')):
                return link
            elif platform == "linkedin":
                if 'linkedin.com' in link:
                    result = f"https://{link}" if not link.startswith('http') else link
                else:
                    clean_link = link.replace('@', '').replace('linkedin.com/in/', '').replace('/', '')
                    result = f"https://linkedin.com/in/{clean_link}"
                print(f"DEBUG: LinkedIn link processed: '{result}'")
                return result
            elif platform == "github":
                if 'github.com' in link:
                    result = f"https://{link}" if not link.startswith('http') else link
                else:
                    clean_link = link.replace('@', '').replace('github.com/', '').replace('/', '')
                    result = f"https://github.com/{clean_link}"
                print(f"DEBUG: GitHub link processed: '{result}'")
                return result
            else:
                if '.' in link and not link.startswith(('http://', 'https://')):
                    result = f"https://{link}"
                else:
                    result = link
                print(f"DEBUG: Generic link processed: '{result}'")
                return result

        professional_links = []
        
        linkedin_raw = safe_get_string("linkedin")
        if linkedin_raw:
            linkedin_processed = process_link(linkedin_raw, "linkedin")
            if linkedin_processed:
                professional_links.append(linkedin_processed)
        
        github_raw = safe_get_string("github") 
        if github_raw:
            github_processed = process_link(github_raw, "github")
            if github_processed:
                professional_links.append(github_processed)
        
        portfolio_raw = safe_get_string("portfolio")
        if portfolio_raw:
            portfolio_processed = process_link(portfolio_raw)
            if portfolio_processed:
                professional_links.append(portfolio_processed)
        
        website_raw = safe_get_string("website")
        if website_raw:
            website_processed = process_link(website_raw)
            if website_processed:
                professional_links.append(website_processed)

        additional_links_raw = safe_get_list("links")
        for link in additional_links_raw:
            if link:
                processed_link = process_link(link)
                if processed_link and processed_link not in professional_links:
                    professional_links.append(processed_link)

        print(f"DEBUG: All professional links collected: {professional_links}")

        for link in professional_links:
            if link:
                try:
                    display_text = link.replace('https://', '').replace('http://', '')
                    
                    if len(display_text) > 40:
                        display_text = display_text[:37] + '...'
                    
                    link_html = f'<a href="{link}" class="contact-link">{display_text}</a>'
                    contact_parts.append(link_html)
                    print(f"DEBUG: Added link to contact_parts: {link_html}")
                except Exception as e:
                    print(f"DEBUG: Error processing link {link}: {e}")

        if contact_parts:
            contact_line = ' | '.join(contact_parts)
            print(f"DEBUG: Final contact line: '{contact_line}'")
        else:
            print("WARNING: No contact parts found - using minimal contact line")
            contact_line = name

        summary = safe_get_string("summary")
        skills = safe_get_list("skills")
        
        photo_html = ""
        photo_data = data.get("photo")
        
        if photo_data:
            try:
                print(f"DEBUG: Processing photo data - type: {type(photo_data)}")
                
                if isinstance(photo_data, str):
                    photo_str = photo_data.strip()
                    
                    if photo_str.startswith('data:image/'):
                        photo_html = f'<div class="photo-container"><img src="{photo_str}" class="profile-photo" alt="Profile Photo"></div>'
                        print("DEBUG: Added data URI photo")
                    elif photo_str.startswith(('http://', 'https://')):
                        photo_html = f'<div class="photo-container"><img src="{photo_str}" class="profile-photo" alt="Profile Photo"></div>'
                        print("DEBUG: Added URL photo")
                    elif len(photo_str) > 100 and ('/' in photo_str or '+' in photo_str):
                        if photo_str.startswith('/9j/'):
                            data_uri = f'data:image/jpeg;base64,{photo_str}'
                        elif photo_str.startswith('iVBORw0KGgo'):
                            data_uri = f'data:image/png;base64,{photo_str}'
                        else:
                            data_uri = f'data:image/jpeg;base64,{photo_str}'
                        
                        photo_html = f'<div class="photo-container"><img src="{data_uri}" class="profile-photo" alt="Profile Photo"></div>'
                        print("DEBUG: Added base64 photo with generated data URI")
                    else:
                        photo_html = '<div class="photo-container"><div class="photo-placeholder">Photo</div></div>'
                        print("DEBUG: Added photo placeholder due to unclear photo format")
                
                elif isinstance(photo_data, bytes):
                    import base64
                    img_data = base64.b64encode(photo_data).decode('utf-8')
                    data_uri = f'data:image/jpeg;base64,{img_data}'
                    photo_html = f'<div class="photo-container"><img src="{data_uri}" class="profile-photo" alt="Profile Photo"></div>'
                    print("DEBUG: Added bytes photo")
                
                else:
                    photo_html = '<div class="photo-container"><div class="photo-placeholder">Photo</div></div>'
                    print(f"DEBUG: Added placeholder for unsupported photo type: {type(photo_data)}")
                    
            except Exception as e:
                print(f"DEBUG: Photo processing error: {e}")
                photo_html = '<div class="photo-container"><div class="photo-placeholder">Photo</div></div>'

        def list_items(items: List[str]) -> str:
            if not items:
                return ""
            li = "".join(f"<li>{item}</li>" for item in items if item)
            return f"<ul class='bullet-list'>{li}</ul>"

        exp_html = ""
        experiences = data.get("experience", [])
        print(f"DEBUG: Processing {len(experiences) if isinstance(experiences, list) else 0} experience entries")
        
        if isinstance(experiences, list):
            for i, exp in enumerate(experiences):
                if not isinstance(exp, dict):
                    print(f"DEBUG: Skipping experience {i} - not a dict")
                    continue
                
                title = str(exp.get("title", "")).strip()
                company = str(exp.get("company", "")).strip()
                eloc = str(exp.get("location", "")).strip()
                start = str(exp.get("start", "")).strip()
                end = str(exp.get("end", "")).strip()
                
                print(f"DEBUG: Experience {i}: {title} at {company}")
                
                if not title and not company:
                    print(f"DEBUG: Skipping experience {i} - no title or company")
                    continue
                
                header_left = join_nonempty([title, company], sep=" at ")
                header_right = join_nonempty([start, end], sep=" - ")
                location_line = f"<div class='item-location'>{eloc}</div>" if eloc else ""
                
                bullets = exp.get("bullets", [])
                if isinstance(bullets, list):
                    bullets = [str(b).strip() for b in bullets if b and str(b).strip()]
                else:
                    bullets = []
                
                print(f"DEBUG: Experience {i} has {len(bullets)} bullets")
                
                exp_html += f"""
                <div class='experience-item'>
                    <div class='item-header'>
                        <h3 class='item-title'>{header_left}</h3>
                        <span class='item-date'>{header_right}</span>
                    </div>
                    {location_line}
                    {list_items(bullets)}
                </div>
                """

        edu_html = ""
        educations = data.get("education", [])
        print(f"DEBUG: Processing {len(educations) if isinstance(educations, list) else 0} education entries")
        
        if isinstance(educations, list):
            for i, ed in enumerate(educations):
                if not isinstance(ed, dict):
                    continue
                
                degree = str(ed.get("degree", "")).strip()
                school = str(ed.get("school", "")).strip()
                eloc = str(ed.get("location", "")).strip()
                year = str(ed.get("year", "")).strip()
                
                print(f"DEBUG: Education {i}: {degree} at {school}")
                
                if not degree and not school:
                    continue
                
                header_left = join_nonempty([degree, school], sep=" - ")
                location_line = f"<div class='item-location'>{eloc}</div>" if eloc else ""
                
                details = ed.get("details", [])
                if isinstance(details, list):
                    details = [str(b).strip() for b in details if b and str(b).strip()]
                else:
                    details = []
                
                edu_html += f"""
                <div class='education-item'>
                    <div class='item-header'>
                        <h3 class='item-title'>{header_left}</h3>
                        <span class='item-date'>{year}</span>
                    </div>
                    {location_line}
                    {list_items(details) if details else ""}
                </div>
                """

        proj_html = ""
        projects = data.get("projects", [])
        if isinstance(projects, list):
            for pr in projects:
                if not isinstance(pr, dict):
                    continue
                
                pname = str(pr.get("name", "")).strip()
                pdesc = str(pr.get("description", "")).strip()
                
                if not pname:
                    continue
                
                tech = pr.get("tech", [])
                if isinstance(tech, list):
                    tech = [str(t).strip() for t in tech if t and str(t).strip()]
                    tech_line = f"<div class='tech-stack'><strong>Technologies:</strong> {', '.join(tech)}</div>" if tech else ""
                else:
                    tech_line = ""
                
                proj_html += f"""
                <div class='project-item'>
                    <h3 class='item-title'>{pname}</h3>
                    <div class='project-desc'>{pdesc}</div>
                    {tech_line}
                </div>
                """

        certs = safe_get_list("certifications")
        cert_html = list_items(certs)

        skills_html = ""
        if skills:
            print(f"DEBUG: Processing skills: {skills}")
            categorized_skills = {}
            uncategorized_skills = []
            
            for skill in skills:
                skill_str = str(skill).strip()
                if ':' in skill_str:
                    category, skill_list = skill_str.split(':', 1)
                    categorized_skills[category.strip()] = skill_list.strip()
                else:
                    uncategorized_skills.append(skill_str)
            
            if categorized_skills:
                for category, skill_list in categorized_skills.items():
                    skills_html += f"<div class='skill-category'><strong>{category}:</strong> {skill_list}</div>"
            
            if uncategorized_skills:
                skills_html += f"<div class='skill-category'>{', '.join(uncategorized_skills)}</div>"
            
            if not skills_html and skills:
                skills_html = f"<div class='skill-category'>{', '.join([str(s) for s in skills])}</div>"

        print(f"DEBUG: Generated skills HTML: {skills_html}")
        print(f"DEBUG: Final contact line before HTML generation: '{contact_line}'")

        html = f"""
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset='utf-8' />
            <title>ATS Resume - {name}</title>
            <style>
              * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
              }}
              
              body {{
                font-family: 'Calibri', 'Arial', sans-serif;
                font-size: 11pt;
                line-height: 1.4;
                color: #2c3e50;
                background: white;
                margin: 0;
                padding: 20px;
              }}
              
              .resume-container {{
                max-width: 8.5in;
                margin: 0 auto;
                background: white;
                position: relative;
              }}
              
              .header-section {{
                text-align: left;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 2px solid #3498db;
                position: relative;
              }}
              
              .header-main {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 10px;
              }}
              
              .header-info {{
                flex: 1;
                text-align: left;
              }}
              
              .photo-container {{
                width: 80px;
                height: 80px;
                margin-left: 15px;
                flex-shrink: 0;
              }}
              
              .profile-photo {{
                width: 100%;
                height: 100%;
                border-radius: 50%;
                object-fit: cover;
                border: 2px solid #3498db;
              }}
              
              .photo-placeholder {{
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: #ecf0f1;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 9pt;
                color: #7f8c8d;
                border: 2px solid #bdc3c7;
              }}
              
              .candidate-name {{
                font-size: 24pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
              }}
              
              .contact-info {{
                font-size: 10pt;
                color: #34495e;
                line-height: 1.4;
              }}
              
              .contact-link {{
                color: #3498db;
                text-decoration: none;
              }}
              
              .contact-link:hover {{
                text-decoration: underline;
              }}
              
              .contact-item {{
                color: #34495e;
              }}
              
              .section {{
                margin-bottom: 20px;
              }}
              
              .section-title {{
                font-size: 14pt;
                font-weight: bold;
                color: #2c3e50;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid #3498db;
                padding-bottom: 3px;
                margin-bottom: 12px;
              }}
              
              .summary-content {{
                text-align: justify;
                margin-bottom: 15px;
                font-size: 11pt;
                line-height: 1.5;
              }}
              
              .skills-content {{
                margin-bottom: 15px;
              }}
              
              .skill-category {{
                margin-bottom: 8px;
                font-size: 11pt;
                line-height: 1.4;
              }}
              
              .skill-category strong {{
                color: #2c3e50;
              }}
              
              .item-header {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                margin-bottom: 4px;
              }}
              
              .item-title {{
                font-size: 12pt;
                font-weight: bold;
                color: #2c3e50;
                flex: 1;
              }}
              
              .item-date {{
                font-size: 10pt;
                color: #7f8c8d;
                font-weight: normal;
                white-space: nowrap;
                margin-left: 10px;
              }}
              
              .item-location {{
                font-size: 10pt;
                color: #7f8c8d;
                font-style: italic;
                margin-bottom: 6px;
              }}
              
              .experience-item,
              .education-item,
              .project-item {{
                margin-bottom: 15px;
                page-break-inside: avoid;
              }}
              
              .bullet-list {{
                margin: 6px 0 0 20px;
                padding: 0;
              }}
              
              .bullet-list li {{
                margin-bottom: 3px;
                text-align: justify;
                font-size: 10.5pt;
                line-height: 1.4;
              }}
              
              .project-desc {{
                font-size: 10.5pt;
                margin-bottom: 6px;
                text-align: justify;
                line-height: 1.4;
              }}
              
              .tech-stack {{
                font-size: 10pt;
                color: #7f8c8d;
                font-style: italic;
              }}
              
              .certifications-content .bullet-list {{
                margin-left: 0;
              }}
              
              .certifications-content .bullet-list li {{
                list-style-type: none;
                margin-bottom: 4px;
                padding-left: 15px;
                position: relative;
              }}
              
              .certifications-content .bullet-list li:before {{
                content: "▪";
                color: #3498db;
                position: absolute;
                left: 0;
              }}
              
              @page {{
                size: A4;
                margin: 0.75in;
              }}
              
              @media print {{
                body {{
                  padding: 0;
                  background: white;
                }}
                
                .resume-container {{
                  max-width: none;
                  box-shadow: none;
                }}
                
                .header-section {{
                  break-after: avoid;
                }}
                
                .section {{
                  break-inside: avoid;
                }}
                
                .experience-item,
                .education-item,
                .project-item {{
                  break-inside: avoid;
                }}
                
                .contact-link {{
                  color: #3498db !important;
                }}
              }}
              
              @media (max-width: 600px) {{
                .header-main {{
                  flex-direction: column;
                  text-align: center;
                }}
                
                .photo-container {{
                  margin: 10px auto 0;
                }}
                
                .header-info {{
                  text-align: center;
                }}
                
                .item-header {{
                  flex-direction: column;
                  align-items: flex-start;
                }}
                
                .item-date {{
                  margin-left: 0;
                  margin-top: 2px;
                }}
              }}
            </style>
            </head>
          <body>
            <div class="resume-container">
              <div class="header-section">
                <div class="header-main">
                  <div class="header-info">
                    <h1 class="candidate-name">{name}</h1>
                    <div class="contact-info">{contact_line}</div>
                  </div>
                  {photo_html}
                </div>
              </div>
              
              {f'<div class="section"><h2 class="section-title">Professional Summary</h2><div class="summary-content">{summary}</div></div>' if summary else ''}
              
              {f'<div class="section"><h2 class="section-title">Core Skills</h2><div class="skills-content">{skills_html}</div></div>' if skills_html else ''}
              
              {f'<div class="section"><h2 class="section-title">Professional Experience</h2>{exp_html}</div>' if exp_html else ''}
              
              {f'<div class="section"><h2 class="section-title">Education</h2>{edu_html}</div>' if edu_html else ''}
              
              {f'<div class="section"><h2 class="section-title">Key Projects</h2>{proj_html}</div>' if proj_html else ''}
              
              {f'<div class="section"><h2 class="section-title">Certifications</h2><div class="certifications-content">{cert_html}</div></div>' if cert_html else ''}
            </div>
          </body>
        </html>
        """
        
        print("DEBUG: About to generate PDF with contact line:", contact_line[:100] if len(contact_line) > 100 else contact_line)
        
        buf = io.BytesIO()
        try:
            HTML(string=html).write_pdf(
                target=buf,
                stylesheets=[CSS(string="@page { size: A4; margin: 0.75in; }")]
            )
            print("DEBUG: ATS Resume PDF generated successfully with WeasyPrint")
            print(f"DEBUG: PDF size: {len(buf.getvalue())} bytes")
            return buf.getvalue()
        except Exception as e:
            print(f"DEBUG: WeasyPrint error in ATS resume generation: {e}")
            import traceback
            print(traceback.format_exc())

    print("DEBUG: Using ReportLab fallback for ATS resume generation")


def test_contact_info_fix():
    test_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1-234-567-8900",
        "location": "San Francisco, CA", 
        "linkedin": "linkedin.com/in/testuser",
        "github": "github.com/testuser",
        "portfolio": "testuser.dev",
        "website": "https://testuser.com",
        "links": ["https://blog.testuser.com"],
        "summary": "This is a test summary to verify the fix works correctly.",
        "skills": ["Python", "JavaScript", "React"],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Test Company",
                "location": "SF, CA",
                "start": "2020",
                "end": "2023",
                "bullets": ["Developed test applications", "Led test projects"]
            }
        ]
    }
    
    print("=" * 60)
    print("TESTING CONTACT INFO FIX")
    print("=" * 60)
    
    try:
        pdf_data = generate_ats_resume_pdf(test_data)
        print(f"SUCCESS: PDF generated with {len(pdf_data)} bytes")
        print("Check the debug output above to verify contact info processing")
        return pdf_data
    except Exception as e:
        print(f"ERROR: Failed to generate PDF: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def generate_ats_resume_pdf_safe(data):
    print("=== PDF Generation Debug Start ===")
    
    print(f"Step 1 - Input data type: {type(data)}")
    if data is None:
        print("ERROR: Data is None")
        return None
    
    if not isinstance(data, dict):
        print(f"ERROR: Data is not a dictionary, got {type(data)}")
        return None
    
    print(f"Step 1 - Data keys: {list(data.keys())}")
    
    try:
        print("Step 2 - Importing ReportLab...")
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.colors import Color, black, blue
        from io import BytesIO
        print("Step 2 - ReportLab imported successfully")
    except ImportError as e:
        print(f"ERROR Step 2 - ReportLab import failed: {e}")
        print("Please run: pip install reportlab")
        return None
    
    try:
        print("Step 3 - Creating PDF canvas...")
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        print(f"Step 3 - Canvas created, size: {width}x{height}")
    except Exception as e:
        print(f"ERROR Step 3 - Canvas creation failed: {e}")
        return None
    
    def draw_section_header(canvas, text, x, y, width=500, color_rgb=(0.2, 0.4, 0.6)):
        canvas.setStrokeColorRGB(0.7, 0.7, 0.7)
        canvas.setLineWidth(0.5)
        canvas.line(x, y + 5, x + width, y + 5)
        
        canvas.setFillColorRGB(*color_rgb)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(x, y - 10, text)
        canvas.setFillColorRGB(0, 0, 0)
        canvas.setStrokeColorRGB(0, 0, 0)
        return y - 28
    
    def draw_job_header(canvas, title, company, dates, location, x, y):
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(x, y, title.upper())
        
        canvas.setFont("Helvetica", 10)
        company_dates = f"{company} | {dates}"
        canvas.drawString(x, y - 12, company_dates)
        
        if location:
            canvas.setFont("Helvetica-Oblique", 9)
            canvas.drawString(x, y - 24, location)
            return y - 36
        return y - 24
    
    def draw_bullet_points(canvas, points, x, y, max_width=500):
        canvas.setFont("Helvetica", 10)
        for point in points:
            if isinstance(point, str) and point.strip():
                words = point.strip().split()
                lines = []
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    if canvas.stringWidth(test_line, "Helvetica", 10) <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                        else:
                            lines.append(word)
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                canvas.drawString(x, y, f"• {lines[0]}")
                y -= 12
                
                for line in lines[1:]:
                    canvas.drawString(x + 8, y, line)
                    y -= 12
                
                y -= 2
        
        return y
    
    def draw_link(canvas, text, url, x, y):
        canvas.setFillColorRGB(0, 0, 0.8)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(x, y, text)
        link_width = canvas.stringWidth(text, "Helvetica", 10)
        canvas.linkURL(url, (x, y-2, x+link_width, y+10))
        canvas.setFillColorRGB(0, 0, 0)
        return x + link_width + 15
    
    try:
        print("Step 4 - Drawing content...")
        y_pos = height - 60
        left_margin = 72
        max_width = width - 144
        
        print("Step 4.1 - Drawing header...")
        personal = data.get('personal_info', {})
        
        if personal:
            c.setFillColorRGB(0.2, 0.4, 0.6)
            c.setFont("Helvetica-Bold", 24)
            full_name = str(personal.get('full_name', personal.get('name', 'Name Not Provided')))
            c.drawString(left_margin, y_pos, full_name)
            y_pos -= 30
            
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 11)
            
            contact_parts = []
            email = personal.get('email', '')
            phone = personal.get('phone', '')
            location = personal.get('location', '')
            
            if email:
                contact_parts.append(email)
            if phone:
                contact_parts.append(phone)
            if location:
                contact_parts.append(location)
            
            if contact_parts:
                contact_line = " | ".join(contact_parts)
                c.drawString(left_margin, y_pos, contact_line)
                y_pos -= 15
            
            links = data.get('professional_links', {})
            
            linkedin = (links.get('linkedin') or links.get('LinkedIn') or 
                       data.get('linkedin') or data.get('LinkedIn') or
                       data.get('linkedin_url') or data.get('linkedin_profile') or '')
            
            github = (links.get('github') or links.get('GitHub') or
                     data.get('github') or data.get('GitHub') or  
                     data.get('github_url') or data.get('github_profile') or '')
            
            portfolio = (links.get('portfolio') or links.get('website') or links.get('Portfolio') or
                        data.get('portfolio') or data.get('website') or data.get('Portfolio') or
                        data.get('portfolio_url') or data.get('website_url') or '')
            
            print(f"DEBUG - All data keys: {list(data.keys())}")
            print(f"DEBUG - Links object: {links}")
            print(f"DEBUG - LinkedIn found: '{linkedin}'")
            print(f"DEBUG - GitHub found: '{github}'") 
            print(f"DEBUG - Portfolio found: '{portfolio}'")
            
            if linkedin or github or portfolio:
                c.setFont("Helvetica", 10)
                c.setFillColorRGB(0, 0, 0.8)
                
                link_parts = []
                
                if linkedin and str(linkedin).strip():
                    if 'linkedin.com/in/' in str(linkedin):
                        username = str(linkedin).split('linkedin.com/in/')[-1].strip('/')
                        display_text = f"linkedin.com/in/{username}"
                    elif str(linkedin).startswith('http'):
                        display_text = str(linkedin)
                    else:
                        display_text = f"linkedin.com/in/{linkedin}"
                    link_parts.append(display_text)
                
                if github and str(github).strip():
                    if 'github.com/' in str(github):
                        username = str(github).split('github.com/')[-1].strip('/')
                        display_text = f"github.com/{username}"
                    elif str(github).startswith('http'):
                        display_text = str(github)
                    else:
                        display_text = f"github.com/{github}"
                    link_parts.append(display_text)
                
                if portfolio and str(portfolio).strip():
                    display_url = str(portfolio).replace('https://', '').replace('http://', '').strip('/')
                    link_parts.append(display_url)
                
                if link_parts:
                    links_text = " | ".join(link_parts)
                    c.drawString(left_margin, y_pos, links_text)
                    print(f"DEBUG - Displaying links: {links_text}")
                    y_pos -= 25
                else:
                    print("DEBUG - No valid link parts created")
                    y_pos -= 5
                
                c.setFillColorRGB(0, 0, 0)
            else:
                print("DEBUG - No links found at all")
                y_pos -= 5
        
        print("Step 4.2 - Drawing profile...")
        print(f"DEBUG - All data keys for summary: {list(data.keys())}")
        
        summary = (data.get('professional_summary') or 
                  data.get('summary') or 
                  data.get('profile') or 
                  data.get('objective') or
                  data.get('Professional_Summary') or
                  data.get('Summary') or
                  data.get('Profile') or
                  data.get('about') or
                  data.get('description') or '')
        
        print(f"DEBUG - Summary found: '{summary}' (length: {len(str(summary)) if summary else 0})")
        
        if summary and str(summary).strip():
            y_pos = draw_section_header(c, "Profile", left_margin, y_pos, max_width)
            
            c.setFont("Helvetica", 11)
            summary_text = str(summary).strip()
            words = summary_text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                if c.stringWidth(test_line, "Helvetica", 11) <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                c.drawString(left_margin, y_pos, line)
                y_pos -= 14
            
            y_pos -= 15
            print(f"DEBUG - Profile section drawn with {len(lines)} lines")
        else:
            y_pos = draw_section_header(c, "Profile", left_margin, y_pos, max_width)
            c.setFont("Helvetica-Oblique", 10)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(left_margin, y_pos, "No professional summary provided in data")
            c.setFillColorRGB(0, 0, 0)
            y_pos -= 25
            print("DEBUG - No summary found, showing placeholder")
        
        print("Step 4.3 - Drawing experience...")
        experiences = (data.get('work_experience') or 
                      data.get('experience') or 
                      data.get('employment') or 
                      data.get('jobs') or [])
        
        if experiences and isinstance(experiences, list) and len(experiences) > 0:
            y_pos = draw_section_header(c, "Experience", left_margin, y_pos, max_width)
            
            for exp in experiences:
                if y_pos < 150:
                    c.showPage()
                    y_pos = height - 60
                
                job_title = str(exp.get('job_title', exp.get('title', 'Job Title')))
                company = str(exp.get('company', 'Company'))
                start_date = str(exp.get('start_date', ''))
                end_date = str(exp.get('end_date', 'Present'))
                dates = f"{start_date} - {end_date}" if start_date else end_date
                location = exp.get('location', '')
                
                y_pos = draw_job_header(c, job_title, company, dates, location, left_margin, y_pos)
                
                description = exp.get('work_description', exp.get('description', ''))
                if description:
                    if '. ' in description:
                        bullet_points = [s.strip() + '.' for s in description.split('. ') if s.strip()]
                    else:
                        bullet_points = [description]
                    
                    y_pos = draw_bullet_points(c, bullet_points, left_margin, y_pos, max_width - 20)
                    y_pos -= 15
        
        print("Step 4.4 - Drawing education...")
        education = (data.get('education') or 
                    data.get('education_history') or 
                    data.get('academic') or [])
        
        if education and isinstance(education, list) and len(education) > 0:
            if y_pos < 200:
                c.showPage()
                y_pos = height - 60
            
            y_pos = draw_section_header(c, "Education", left_margin, y_pos, max_width)
            
            for edu in education:
                degree = str(edu.get('degree', 'Degree'))
                year = str(edu.get('year', ''))
                school = str(edu.get('school', edu.get('university', 'School')))
                edu_location = edu.get('location', '')
                
                c.setFont("Helvetica-Bold", 11)
                edu_header = degree.upper()
                if year:
                    edu_header += f" | {year}"
                
                c.drawString(left_margin, y_pos, edu_header)
                y_pos -= 12
                
                c.setFont("Helvetica", 10)
                school_line = school
                if edu_location:
                    school_line += f", {edu_location}"
                
                c.drawString(left_margin, y_pos, school_line)
                y_pos -= 12
                
                details = edu.get('additional_details', '')
                if details:
                    c.setFont("Helvetica", 9)
                    c.drawString(left_margin, y_pos, details)
                    y_pos -= 12
                
                y_pos -= 8
        
        print("Step 4.5 - Drawing skills...")
        skills = (data.get('skills') or 
                 data.get('technical_skills') or 
                 data.get('abilities') or 
                 data.get('competencies') or '')
        
        if skills and str(skills).strip():
            if y_pos < 100:
                c.showPage()
                y_pos = height - 60
            
            y_pos = draw_section_header(c, "Skills & Abilities", left_margin, y_pos, max_width)
            
            if isinstance(skills, str):
                skills_list = [s.strip() for s in skills.split(',') if s.strip()]
            else:
                skills_list = skills if isinstance(skills, list) else [str(skills)]
            
            c.setFont("Helvetica", 10)
            
            for skill in skills_list:
                c.drawString(left_margin, y_pos, f"• {skill.strip()}")
                y_pos -= 12
            
            y_pos -= 10
        
        print("Step 4.6 - Drawing projects...")
        projects = (data.get('projects') or 
                   data.get('portfolio') or 
                   data.get('work_samples') or [])
        
        if projects and isinstance(projects, list) and len(projects) > 0:
            if y_pos < 150:
                c.showPage()
                y_pos = height - 60
            
            y_pos = draw_section_header(c, "Projects", left_margin, y_pos, max_width)
            
            for project in projects:
                project_name = str(project.get('project_name', project.get('name', 'Project')))
                technologies = project.get('technologies_used', project.get('technologies', ''))
                description = project.get('description', '')
                
                c.setFont("Helvetica-Bold", 11)
                c.drawString(left_margin, y_pos, project_name.upper())
                y_pos -= 12
                
                if technologies:
                    c.setFont("Helvetica-Oblique", 9)
                    c.drawString(left_margin, y_pos, f"Technologies: {technologies}")
                    y_pos -= 12
                
                if description:
                    y_pos = draw_bullet_points(c, [description], left_margin, y_pos, max_width - 20)
                
                y_pos -= 10
        
        print("Step 4.7 - Drawing additional sections...")
        additional = data.get('additional_sections', {})
        
        certifications = (additional.get('certifications') or 
                         data.get('certifications') or 
                         data.get('certificates') or [])
        
        if certifications and (isinstance(certifications, list) and len(certifications) > 0 or 
                              isinstance(certifications, str) and certifications.strip()):
            if y_pos < 100:
                c.showPage()
                y_pos = height - 60
            
            y_pos = draw_section_header(c, "Certifications", left_margin, y_pos, max_width)
            
            if isinstance(certifications, str):
                certifications = [cert.strip() for cert in certifications.split(',') if cert.strip()]
            
            y_pos = draw_bullet_points(c, certifications, left_margin, y_pos, max_width)
            y_pos -= 10
        
        languages = (additional.get('languages') or 
                    data.get('languages') or 
                    data.get('language_skills') or [])
        
        if languages and (isinstance(languages, list) and len(languages) > 0 or 
                         isinstance(languages, str) and languages.strip()):
            if isinstance(languages, str):
                languages = [lang.strip() for lang in languages.split(',') if lang.strip()]
            
            y_pos = draw_section_header(c, "Languages", left_margin, y_pos, max_width)
            y_pos = draw_bullet_points(c, languages, left_margin, y_pos, max_width)
            y_pos -= 10
        
        awards = (additional.get('awards') or 
                 additional.get('honors') or
                 data.get('awards') or 
                 data.get('honors') or 
                 data.get('achievements') or [])
        
        if awards and (isinstance(awards, list) and len(awards) > 0 or 
                      isinstance(awards, str) and awards.strip()):
            if isinstance(awards, str):
                awards = [award.strip() for award in awards.split(',') if award.strip()]
            
            y_pos = draw_section_header(c, "Awards & Honors", left_margin, y_pos, max_width)
            y_pos = draw_bullet_points(c, awards, left_margin, y_pos, max_width)
            y_pos -= 10
        
        interests = (additional.get('interests') or 
                    additional.get('hobbies') or
                    data.get('interests') or 
                    data.get('hobbies') or 
                    data.get('activities') or '')
        
        if interests and str(interests).strip():
            y_pos = draw_section_header(c, "Activities and Interests", left_margin, y_pos, max_width)
            
            if isinstance(interests, list):
                interests_text = ', '.join([str(i) for i in interests if str(i).strip()])
            else:
                interests_text = str(interests).strip()
            
            if interests_text:
                c.setFont("Helvetica", 10)
                c.drawString(left_margin, y_pos, interests_text)
        
        print("Step 4 - All content drawn successfully")
        
    except Exception as e:
        print(f"ERROR Step 4 - Content drawing failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    try:
        print("Step 5 - Saving PDF...")
        c.save()
        buffer.seek(0)
        print("Step 5 - PDF saved successfully")
        print(f"Step 5 - Buffer size: {len(buffer.getvalue())} bytes")
        return buffer
    except Exception as e:
        print(f"ERROR Step 5 - PDF save failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_pdf_report_safe(data):
    return generate_ats_resume_pdf_safe(data)

def test_clean_professional():
    print("\n=== Testing with clean professional format ===")
    
    clean_data = {
        'personal_info': {
            'full_name': 'May Riley',
            'email': 'm.riley@live.com',
            'phone': '(716) 555-0100',
            'location': '4567 Main Street, Buffalo, New York 98052'
        },
        'professional_links': {
            'linkedin': 'https://www.linkedin.com/in/m-riley',
            'github': 'https://github.com/mriley',
            'portfolio': 'https://mriley-portfolio.com'
        },
        'professional_summary': 'Friendly and engaging team player and leader able to inspire staff to perform their best. Detail oriented and experienced restaurant manager, passionate about food and beverages. A multi-tasker who excels at staff training and recruiting with a track record of inspiring great customer service and customer satisfaction. Regularly exceed sales goals. A master in the art of upselling.',
        'work_experience': [
            {
                'job_title': 'Restaurant Manager',
                'company': 'CONTOSO BAR AND GRILL',
                'start_date': 'SEPTEMBER 20XX',
                'end_date': 'PRESENT',
                'location': '',
                'work_description': 'Recruit, hire, train, and coach over 30 staff members on customer service skills, food & beverage knowledge, and menu items. Reduced costs by 7% through controls on overtime, operational efficiencies, and reduced waste. Consistently exceed monthly sales goals by a minimum of 10% by training FOH staff on upselling techniques and by creating a featured food and beverage program.'
            },
            {
                'job_title': 'Restaurant Manager',
                'company': 'FOURTH COFFEE BISTRO',
                'start_date': 'JUNE 20XX',
                'end_date': 'AUGUST 20XX',
                'location': '',
                'work_description': 'Created a cross-training program ensuring FOH staff members were able to perform confidently and effectively in all positions. Grew customer based and increased restaurant social media accounts by 19% through interactive promotional campaigns, engaging staff contests. Created and implemented staff health and safety standards compliance training program, achieving a score of 99% from the Board of Health. Successfully redesigned existing inventory system, ordering and food storage practices, resulting in a 6% decrease in food waste and higher net profits.'
            }
        ],
        'education': [
            {
                'degree': 'B.S. IN BUSINESS ADMINISTRATION',
                'year': 'JUNE 20XX',
                'school': 'BIGTOWN COLLEGE',
                'location': 'CHICAGO, ILLINOIS',
                'additional_details': ''
            },
            {
                'degree': 'A.A. IN HOSPITALITY MANAGEMENT',
                'year': 'JUNE 20XX',
                'school': 'BIGTOWN COLLEGE',
                'location': 'CHICAGO, ILLINOIS',
                'additional_details': ''
            }
        ],
        'skills': 'Accounting & budgeting, Proficient with POS systems, Excellent interpersonal and communication skills, Poised under pressure, Experienced in most restaurant positions, Fun and energetic',
        'additional_sections': {
            'interests': ['Theater', 'environmental conservation', 'art', 'hiking', 'skiing', 'travel']
        }
    }
    
    result = generate_ats_resume_pdf_safe(clean_data)
    
    if result:
        print("SUCCESS: Clean professional test passed!")
        try:
            with open('clean_professional_resume.pdf', 'wb') as f:
                f.write(result.getvalue())
            print("Clean professional resume PDF saved as 'clean_professional_resume.pdf'")
        except Exception as e:
            print(f"Could not save file: {e}")
    else:
        print("FAILED: Clean professional test failed")

def test_debug_data():
    print("\n=== Debugging Your Data Structure ===")
    
    your_data = {
        'personal_info': {
            'full_name': 'John Superb',
            'email': 'superbjohn@gmail.com',
            'phone': '+911234567890',
            'location': 'Bengaluru, India'
        },
        'professional_links': {
            'linkedin': 'https://linkedin.com/in/superbjohn',
            'github': 'https://github.com/superbjohn',
            'portfolio': 'https://superbjohn.dev'
        },
        'professional_summary': 'Experienced software developer with expertise in full-stack development, cloud technologies, and DevOps practices. Passionate about creating scalable solutions and mentoring junior developers.',
        'work_experience': [
            {
                'job_title': 'Senior Software Engineer',
                'company': 'Tech Company India',
                'start_date': 'Jan 2022',
                'end_date': 'Present',
                'location': 'Bengaluru, India',
                'work_description': 'Led development of microservices architecture. Implemented CI/CD pipelines. Mentored 5+ junior developers.'
            }
        ],
        'education': [
            {
                'degree': 'B.Tech in Computer Science',
                'year': '2020',
                'school': 'Indian Institute of Technology',
                'location': 'Bengaluru, India'
            }
        ],
        'skills': 'Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, MongoDB, PostgreSQL'
    }
    
    print("Testing with your data structure...")
    result = generate_ats_resume_pdf_safe(your_data)
    
    if result:
        print("SUCCESS: Debug test passed!")
        try:
            with open('debug_resume.pdf', 'wb') as f:
                f.write(result.getvalue())
            print("Debug resume PDF saved as 'debug_resume.pdf'")
        except Exception as e:
            print(f"Could not save file: {e}")
    else:
        print("FAILED: Debug test failed")
    
    return result

def test_links_only():
    """Test specifically for links display"""
    print("\n=== Testing Links Display Only ===")
    
    links_data = {
        'personal_info': {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'location': 'Test City'
        },
        'linkedin': 'https://linkedin.com/in/testuser',
        'github': 'https://github.com/testuser',
        'portfolio': 'https://testuser.dev',
        'professional_links': {
            'linkedin': 'https://linkedin.com/in/testuser',
            'github': 'https://github.com/testuser', 
            'portfolio': 'https://testuser.dev'
        },
        'professional_summary': 'This is a test professional summary to verify the profile section displays correctly.'
    }
    
    result = generate_ats_resume_pdf_safe(links_data)
    
    if result:
        print("SUCCESS: Links test passed!")
        try:
            with open('links_test.pdf', 'wb') as f:
                f.write(result.getvalue())
            print("Links test PDF saved as 'links_test.pdf'")
        except Exception as e:
            print(f"Could not save file: {e}")
    
    return result

# Expected data structure (same as before but cleaner formatting)
"""
Expected data structure for clean professional resume:

{
    'personal_info': {
        'full_name': 'Your Full Name',
        'email': 'your.email@example.com',
        'phone': '(555) 123-4567',
        'location': 'Full Address or City, State'
    },
    'professional_links': {
        'linkedin': 'https://linkedin.com/in/yourprofile',
        'github': 'https://github.com/yourusername',
        'portfolio': 'https://yourwebsite.com'
    },
    'professional_summary': 'Your professional summary paragraph...',
    'work_experience': [
        {
            'job_title': 'Your Job Title',
            'company': 'COMPANY NAME',
            'start_date': 'START DATE',
            'end_date': 'END DATE or PRESENT',
            'location': 'Location (optional)',
            'work_description': 'Detailed description of accomplishments and responsibilities...'
        }
    ],
    'education': [
        {
            'degree': 'DEGREE NAME',
            'year': 'GRADUATION YEAR',
            'school': 'SCHOOL NAME',
            'location': 'CITY, STATE',
            'additional_details': 'Optional additional info'
        }
    ],
    'skills': 'Skill 1, Skill 2, Skill 3, Skill 4, Skill 5, Skill 6',
    'projects': [
        {
            'project_name': 'Project Name',
            'description': 'Project description...',
            'technologies_used': 'Technology stack used'
        }
    ],
    'additional_sections': {
        'certifications': ['Certification 1', 'Certification 2'],
        'languages': ['Language 1 (Level)', 'Language 2 (Level)'],
        'awards': ['Award 1', 'Award 2'],
        'interests': ['Interest 1', 'Interest 2', 'Interest 3']
    }
}
"""

# Uncomment to run test:
# test_clean_professional()

# To debug your actual data:
# debug_your_data(your_actual_data_here)


def generate_pdf_report_safe(data):
    try:
        # Add actual PDF generation logic here
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        filename = "report.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        c.drawString(100, 750, "Report Generated")
        c.save()
        return filename
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_contact_info_fix()



