from dataclasses import dataclass
from typing import List, Dict, Any
import re

# Lightweight skills glossary with categories (extend as needed)
SKILL_BANK = {
    "programming": ["python", "java", "c++", "c", "javascript", "typescript", "go", "rust"],
    "web": ["html", "css", "react", "node", "express", "django", "flask", "spring", "angular"],
    "data": ["sql", "mysql", "postgres", "mongodb", "pandas", "numpy", "scikit-learn", "pyspark"],
    "cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd"],
    "ml": ["machine learning", "deep learning", "nlp", "computer vision", "transformers"],
    "tools": ["git", "jira", "linux", "bash", "graphql", "rest api"],
}

def normalize_tokens(text: str) -> List[str]:
    text = text.lower()
    # keep words and plus signs (for c++)
    tokens = re.findall(r"[a-zA-Z\+\#\.]{2,}", text)
    return tokens

@dataclass
class AnalysisResult:
    found_skills: Dict[str, List[str]]
    unique_skills: List[str]
    key_phrases: List[str]

class AnalyzerAgent:
    """
    Extracts skills and phrases from resume/job texts using a small glossary + regex.
    """
    def extract_skills(self, text: str) -> AnalysisResult:
        tokens = normalize_tokens(text)
        text_joined = " ".join(tokens)
        found: Dict[str, List[str]] = {}

        unique_hits = set()
        for cat, skills in SKILL_BANK.items():
            hits = []
            for sk in skills:
                # allow multiword skills
                if re.search(rf"\b{re.escape(sk.lower())}\b", text_joined):
                    hits.append(sk)
                    unique_hits.add(sk)
            if hits:
                found[cat] = sorted(set(hits))

        # naive phrase extraction: top frequent 2-3 word phrases that look technical
        words = [w for w in tokens if len(w) > 2]
        phrases = []
        for i in range(len(words)-1):
            bigram = f"{words[i]} {words[i+1]}"
            if any(k in bigram for k in ["machine", "learning", "deep", "neural", "cloud", "data", "model"]):
                phrases.append(bigram)
        phrases = sorted(list(set(phrases)))[:20]

        return AnalysisResult(found_skills=found, unique_skills=sorted(unique_hits), key_phrases=phrases)

    def skill_gap(self, resume_skills: List[str], job_skills: List[str]) -> Dict[str, List[str]]:
        missing = [s for s in job_skills if s not in set(resume_skills)]
        overlap = [s for s in job_skills if s in set(resume_skills)]
        extras = [s for s in resume_skills if s not in set(job_skills)]
        return {"missing": sorted(missing), "overlap": sorted(overlap), "extras": sorted(extras)}
