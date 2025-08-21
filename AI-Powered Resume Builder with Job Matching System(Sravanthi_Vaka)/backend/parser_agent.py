from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import pdfplumber
import re

@dataclass
class ParseResult:
    raw_text: str
    sections: Dict[str, str]
    bullets: List[str]

class ParserAgent:
    """
    Extracts text from resume PDF and normalizes job description text.
    Also attempts naive sectioning (Experience/Education/Skills/Projects).
    """
    SECTION_KEYS = ["experience", "education", "skills", "projects", "summary", "certifications"]

    def _read_pdf(self, file_path: str) -> str:
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n\n", text)
        return text.strip()

    def _split_bullets(self, text: str) -> List[str]:
        # split on lines starting with dash/bullet or sentences
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        bullets = []
        for ln in lines:
            if re.match(r"^[-•*]\s+", ln):
                bullets.append(re.sub(r"^[-•*]\s+", "", ln))
            else:
                bullets.extend([s.strip() for s in re.split(r"(?<=[.!?])\s+", ln) if len(s.strip()) > 4])
        return bullets

    def _sectionize(self, text: str) -> Dict[str, str]:
        lowered = text.lower()
        positions: List[Tuple[str, int]] = []
        for k in self.SECTION_KEYS:
            m = re.search(rf"\b{k}\b", lowered)
            if m:
                positions.append((k, m.start()))
        if not positions:
            return {"body": text}

        positions.sort(key=lambda x: x[1])
        sections: Dict[str, str] = {}
        for i, (name, start) in enumerate(positions):
            end = positions[i + 1][1] if i + 1 < len(positions) else len(text)
            sections[name] = text[start:end].strip()
        return sections

    def parse_resume_pdf(self, file_path: str) -> ParseResult:
        raw = self._read_pdf(file_path)
        norm = self._normalize_text(raw)
        return ParseResult(raw_text=norm, sections=self._sectionize(norm), bullets=self._split_bullets(norm))

    def parse_job_text(self, text: str) -> ParseResult:
        norm = self._normalize_text(text)
        return ParseResult(raw_text=norm, sections=self._sectionize(norm), bullets=self._split_bullets(norm))
