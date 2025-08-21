from dataclasses import dataclass, field
from typing import List
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

@dataclass
class ResumeData:
    name: str
    email: str
    phone: str
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)  # e.g., "B.Tech in IT, 2021-2025"
    experience: List[str] = field(default_factory=list) # bullet points
    projects: List[str] = field(default_factory=list)   # bullet points

class ResumeBuilder:
    """
    Minimal, clean PDF resume using ReportLab. One-page layout.
    """
    def build_pdf(self, path: str, data: ResumeData):
        c = canvas.Canvas(path, pagesize=LETTER)
        width, height = LETTER
        margin = 0.75 * inch
        x = margin
        y = height - margin

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, data.name)
        y -= 16
        c.setFont("Helvetica", 10)
        c.drawString(x, y, f"{data.email} | {data.phone}")
        y -= 20

        def section(title: str):
            nonlocal y
            y -= 10
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, title)
            y -= 12
            c.setFont("Helvetica", 10)

        def bullets(items: List[str]):
            nonlocal y
            for it in items:
                for line in wrap_text(it, 90):
                    c.drawString(x + 14, y, f"• {line}")
                    y -= 12

        def wrap_text(text: str, max_chars: int) -> List[str]:
            words = text.split()
            lines, curr = [], []
            for w in words:
                if sum(len(t) for t in curr) + len(curr) + len(w) > max_chars:
                    lines.append(" ".join(curr)); curr = [w]
                else:
                    curr.append(w)
            if curr:
                lines.append(" ".join(curr))
            return lines

        if data.summary:
            section("Summary")
            for line in wrap_text(data.summary, 95):
                c.drawString(x, y, line); y -= 12

        if data.skills:
            section("Skills")
            c.drawString(x + 14, y, ", ".join(data.skills)); y -= 14

        if data.education:
            section("Education")
            bullets(data.education)

        if data.experience:
            section("Experience")
            bullets(data.experience)

        if data.projects:
            section("Projects")
            bullets(data.projects)

        c.showPage()
        c.save()
