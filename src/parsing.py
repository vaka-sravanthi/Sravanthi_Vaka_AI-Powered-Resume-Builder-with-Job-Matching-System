from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

import pdfplumber


BASIC_SKILLS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "sql",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "nlp", "spacy", "nltk",
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "git",
    "react", "node", "streamlit", "flask", "django",
    "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
    "jenkins", "ansible", "terraform", "prometheus", "grafana",
    "spring", "hibernate", "express", "vue", "angular",
    "machine learning", "deep learning", "data science", "ai",
    "agile", "scrum", "kanban", "microservices", "rest api",
    "graphql", "oauth", "jwt", "websockets", "grpc"
}


@dataclass
class ResumeData:
    raw_text: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    skills: List[str]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_parts: List[str] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                text_parts.append(txt)
        return "\n".join(text_parts)
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    patterns = [
        r"(\+?\d{1,4}[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4})",
        r"(\+?\d[\d\-\s\(\)]{7,}\d)",
        r"(\d{3}[\-\.\s]?\d{3}[\-\.\s]?\d{4})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def extract_name(text: str) -> Optional[str]:
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if line and 2 <= len(line.split()) <= 5 and len(line) <= 64:
            if not re.search(r'\d{4}|\@|www\.|http|phone|email|address', line.lower()):
                return line
    return None


def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    tokens = set(re.findall(r"[A-Za-z#+.\-]+", text_lower))
    
    matched_skills = []
    
    for skill in BASIC_SKILLS:
        if skill in tokens or skill in text_lower:
            matched_skills.append(skill)
    
    return sorted(list(set(matched_skills)))


def parse_resume_pdf(pdf_bytes: bytes) -> ResumeData:
    raw = extract_text_from_pdf(pdf_bytes)
    return ResumeData(
        raw_text=raw,
        name=extract_name(raw),
        email=extract_email(raw),
        phone=extract_phone(raw),
        skills=extract_skills(raw),
    )


def parse_job_description(text: str) -> Dict[str, List[str]]:
    text = text or ""
    skills = extract_skills(text)
    return {"skills": skills}


def validate_pdf_upload(file) -> Tuple[bool, str]:
    if not file:
        return False, "No file uploaded"
    
    filename = ""
    if hasattr(file, 'name'):
        filename = file.name
    elif hasattr(file, 'filename'):
        filename = file.filename
    else:
        return False, "Unable to determine file name"
    
    if not filename.lower().endswith('.pdf'):
        return False, f"Invalid file type. Expected PDF, got {filename.split('.')[-1] if '.' in filename else 'unknown'}"
    
    if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:
        return False, "File too large. Please upload a file smaller than 10MB"
    
    try:
        file_bytes = file.read()
        if len(file_bytes) < 100:
            return False, "File appears to be corrupted or empty"
        
        if hasattr(file, 'seek'):
            file.seek(0)
            
        if not file_bytes.startswith(b'%PDF'):
            return False, "File does not appear to be a valid PDF"
            
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
    
    return True, ""


def validate_multiple_pdf_uploads(files: List[Any]) -> Tuple[bool, str]:
    if not files or len(files) == 0:
        return False, "No files uploaded"
    
    if len(files) > 20:
        return False, "Too many files. Please upload no more than 20 resumes at once"
    
    total_size = 0
    invalid_files = []
    
    for i, file in enumerate(files):
        is_valid, error_msg = validate_pdf_upload(file)
        if not is_valid:
            invalid_files.append(f"File {i+1} ({getattr(file, 'name', 'unknown')}): {error_msg}")
        
        if hasattr(file, 'size'):
            total_size += file.size
    
    if invalid_files:
        return False, "Invalid files found:\n" + "\n".join(invalid_files)
    
    if total_size > 50 * 1024 * 1024:
        return False, "Total file size too large. Please upload files with combined size less than 50MB"
    
    return True, ""


def parse_multiple_resumes(files: List[Any]) -> List[Tuple[str, ResumeData]]:
    results = []
    
    for file in files:
        try:
            filename = getattr(file, 'name', getattr(file, 'filename', 'unknown.pdf'))
            
            file_bytes = file.read()
            
            if hasattr(file, 'seek'):
                file.seek(0)
            
            resume_data = parse_resume_pdf(file_bytes)
            results.append((filename, resume_data))
            
        except Exception as e:
            print(f"Error parsing {getattr(file, 'name', 'unknown')}: {str(e)}")
            continue
    
    return results


def extract_enhanced_skills(text: str, job_skills: List[str] = None) -> List[str]:
    text_lower = text.lower()
    all_skills = set(BASIC_SKILLS)
    
    if job_skills:
        all_skills.update(skill.lower() for skill in job_skills)
    
    tokens = set(re.findall(r"[A-Za-z#+.\-]+", text_lower))
    
    matched_skills = []
    
    for skill in all_skills:
        if skill in tokens or skill in text_lower:
            matched_skills.append(skill)
    
    skill_patterns = {
        r'python\s*\d+': 'python',
        r'java\s*(se|ee|\d+)': 'java',
        r'\.net\s*(core|framework)?': '.net',
        r'c\s*\+\+': 'c++',
        r'c\s*#': 'c#',
    }
    
    for pattern, skill in skill_patterns.items():
        if re.search(pattern, text_lower):
            matched_skills.append(skill)
    
    return sorted(list(set(matched_skills)))


def get_resume_summary_stats(resume_data: ResumeData) -> Dict[str, Any]:
    text = resume_data.raw_text
    
    return {
        'word_count': len(text.split()),
        'character_count': len(text),
        'line_count': len(text.splitlines()),
        'has_email': bool(resume_data.email),
        'has_phone': bool(resume_data.phone),
        'has_name': bool(resume_data.name),
        'skill_count': len(resume_data.skills),
        'estimated_experience_years': estimate_experience_years(text)
    }


def estimate_experience_years(text: str) -> int:
    years = re.findall(r'\b(19|20)\d{2}\b', text)
    if not years:
        return 0
    
    years = [int(year) for year in years]
    current_year = 2024
    
    if len(years) >= 2:
        min_year = min(years)
        max_year = min(max(years), current_year)
        
        if max_year - min_year <= 50 and max_year - min_year >= 0:
            return max_year - min_year
    
    return 0


def clean_text_for_analysis(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    
    text = re.sub(r'[^\w\s@.\-+#()]', ' ', text)
    
    text = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '', text)
    text = re.sub(r'(\+?\d[\d\-\s\(\)]{7,}\d)', '', text)
    
    return text.strip()