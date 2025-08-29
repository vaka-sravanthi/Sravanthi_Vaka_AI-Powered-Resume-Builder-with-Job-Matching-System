from __future__ import annotations

from typing import List, Tuple, Dict, Any
from src.parsing import ResumeData


def dot(a: List[float], b: List[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


def norm(a: List[float]) -> float:
    return float(sum(x * x for x in a) ** 0.5)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    denom = (norm(a) * norm(b)) or 1.0
    return dot(a, b) / denom


def compute_match_score(
    resume_vec: List[float], 
    job_vec: List[float], 
    resume_skills: List[str], 
    job_skills: List[str]
) -> Dict[str, Any]:
    sim = cosine_similarity(resume_vec, job_vec)
    
    rs = set(s.lower().strip() for s in resume_skills if s.strip())
    js = set(s.lower().strip() for s in job_skills if s.strip())
    
    skill_overlap = len(rs & js)
    skill_union = len(rs | js) or 1
    jaccard = skill_overlap / skill_union
    
    score = 0.7 * sim + 0.3 * jaccard
    score_pct = max(0.0, min(1.0, score)) * 100.0
    
    confidence = 0.5 + 0.5 * min(sim, 1.0)
    
    missing_skills = sorted(list(js - rs))
    matched_skills = sorted(list(rs & js))
    
    explanation = (
        f"Semantic similarity: {sim:.2f}. "
        f"Skill overlap: {skill_overlap}/{len(js)} required skills matched. "
        f"Combined score: {score_pct:.1f}%."
    )
    
    return {
        "similarity": sim,
        "jaccard": jaccard,
        "score": score_pct,
        "confidence": confidence,
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "skill_overlap": skill_overlap,
        "total_required_skills": len(js),
        "total_resume_skills": len(rs),
        "explanation": explanation,
    }


def top_k_matches(
    query_vec: List[float], 
    corpus_texts: List[str], 
    corpus_vecs: List[List[float]], 
    k: int = 5
) -> List[Tuple[str, float]]:
    sims = [
        (text, cosine_similarity(query_vec, vec)) 
        for text, vec in zip(corpus_texts, corpus_vecs)
    ]
    sims.sort(key=lambda x: x[1], reverse=True)
    return sims[:k]


def calculate_resume_job_match(resume_data: ResumeData, job_skills: List[str]) -> Dict[str, Any]:
    resume_skills = resume_data.skills or []
    
    rs = set(s.lower().strip() for s in resume_skills if s.strip())
    js = set(s.lower().strip() for s in job_skills if s.strip())
    
    matched_skills = list(rs & js)
    missing_skills = list(js - rs)
    
    skill_overlap = len(matched_skills)
    total_job_skills = len(js) or 1
    total_resume_skills = len(rs)
    
    skill_match_score = (skill_overlap / total_job_skills) * 100.0
    
    skill_breadth_bonus = min((total_resume_skills / total_job_skills) * 10, 20) if total_job_skills > 0 else 0
    
    final_score = min(skill_match_score + skill_breadth_bonus, 100.0)
    
    return {
        "skill_match_score": final_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "total_job_skills": total_job_skills,
        "total_resume_skills": total_resume_skills,
        "skill_overlap_count": skill_overlap,
        "skill_breadth_bonus": skill_breadth_bonus
    }


def rank_resumes(resume_results: List[Tuple[str, ResumeData]], job_skills: List[str]) -> List[Dict[str, Any]]:
    ranked_resumes = []
    
    for filename, resume_data in resume_results:
        match_result = calculate_resume_job_match(resume_data, job_skills)
        
        ranked_resumes.append({
            'filename': filename,
            'resume_data': resume_data,
            'match_score': match_result['skill_match_score'],
            'matched_skills': match_result['matched_skills'],
            'missing_skills': match_result['missing_skills'],
            'total_skills': match_result['total_resume_skills'],
            'total_job_skills': match_result['total_job_skills'],
            'skill_overlap': match_result['skill_overlap_count'],
            'skill_breadth_bonus': match_result['skill_breadth_bonus']
        })
    
    ranked_resumes.sort(key=lambda x: x['match_score'], reverse=True)
    
    return ranked_resumes


def calculate_detailed_match_metrics(resume_data: ResumeData, job_skills: List[str], job_text: str = "") -> Dict[str, Any]:
    basic_match = calculate_resume_job_match(resume_data, job_skills)
    
    resume_text = resume_data.raw_text.lower()
    
    keyword_matches = []
    if job_text:
        job_keywords = set(word.lower().strip() for word in job_text.split() 
                          if len(word) > 3 and word.isalpha())
        resume_words = set(word.lower().strip() for word in resume_text.split() 
                          if len(word) > 3 and word.isalpha())
        keyword_matches = list(job_keywords & resume_words)
    
    experience_indicators = ['year', 'years', 'experience', 'led', 'managed', 'senior', 'lead']
    experience_score = sum(1 for indicator in experience_indicators if indicator in resume_text)
    
    education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college']
    education_score = sum(1 for keyword in education_keywords if keyword in resume_text)
    
    return {
        **basic_match,
        'keyword_matches': keyword_matches[:10],
        'keyword_match_count': len(keyword_matches),
        'experience_indicators': experience_score,
        'education_score': education_score,
        'resume_word_count': len(resume_data.raw_text.split()),
        'has_contact_info': bool(resume_data.email and resume_data.phone),
        'completeness_score': calculate_resume_completeness(resume_data)
    }


def calculate_resume_completeness(resume_data: ResumeData) -> float:
    score = 0
    max_score = 100
    
    if resume_data.name:
        score += 10
    if resume_data.email:
        score += 10
    if resume_data.phone:
        score += 10
    
    if resume_data.skills and len(resume_data.skills) > 0:
        score += min(25, len(resume_data.skills) * 2)
    
    word_count = len(resume_data.raw_text.split())
    if word_count > 100:
        score += min(20, word_count / 25)
    
    text_lower = resume_data.raw_text.lower()
    experience_keywords = ['experience', 'work', 'job', 'position', 'role', 'company', 'employer']
    experience_mentions = sum(1 for keyword in experience_keywords if keyword in text_lower)
    score += min(25, experience_mentions * 3)
    
    return min(score, max_score)


def compare_resumes(resume1_data: ResumeData, resume2_data: ResumeData, job_skills: List[str]) -> Dict[str, Any]:
    match1 = calculate_resume_job_match(resume1_data, job_skills)
    match2 = calculate_resume_job_match(resume2_data, job_skills)
    
    return {
        'resume1_score': match1['skill_match_score'],
        'resume2_score': match2['skill_match_score'],
        'winner': 'resume1' if match1['skill_match_score'] > match2['skill_match_score'] else 'resume2',
        'score_difference': abs(match1['skill_match_score'] - match2['skill_match_score']),
        'resume1_unique_skills': list(set(match1['matched_skills']) - set(match2['matched_skills'])),
        'resume2_unique_skills': list(set(match2['matched_skills']) - set(match1['matched_skills'])),
        'common_matched_skills': list(set(match1['matched_skills']) & set(match2['matched_skills']))
    }


def get_scoring_insights(ranked_resumes: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not ranked_resumes:
        return {}
    
    scores = [r['match_score'] for r in ranked_resumes]
    skill_counts = [len(r['matched_skills']) for r in ranked_resumes]
    
    return {
        'total_resumes': len(ranked_resumes),
        'average_score': sum(scores) / len(scores),
        'highest_score': max(scores),
        'lowest_score': min(scores),
        'score_range': max(scores) - min(scores),
        'average_matched_skills': sum(skill_counts) / len(skill_counts),
        'top_candidate': ranked_resumes[0]['filename'] if ranked_resumes else None,
        'competitive_candidates': len([r for r in ranked_resumes if r['match_score'] > 70]),
        'qualified_candidates': len([r for r in ranked_resumes if r['match_score'] > 50])
    }