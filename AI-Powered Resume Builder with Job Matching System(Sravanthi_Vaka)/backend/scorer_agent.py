from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np

@dataclass
class ScoreReport:
    score: float                 # 0..100
    confidence: float            # 0..100
    reasoning: List[str]         # plain-language explanations
    factors: Dict[str, float]    # sub-scores

class ScorerAgent:
    """
    Combines semantic similarity with skill overlap coverage to produce
    a recruiter-style score and confidence, plus explainable factors.
    """
    def compute(self,
                similarity: float,
                resume_skills: List[str],
                job_skills: List[str],
                top_pairs: List[tuple]) -> ScoreReport:

        # coverage metrics
        job_set = set(job_skills)
        res_set = set(resume_skills)
        overlap = len(job_set & res_set)
        coverage = (overlap / max(1, len(job_set)))  # 0..1

        # simple weighted scoring
        sim_weight = 0.65
        cov_weight = 0.35
        composite = sim_weight * similarity + cov_weight * coverage

        # confidence heuristic: lower variance among top pair scores => higher confidence
        tp_scores = [p[2] for p in top_pairs] or [similarity]
        conf = 1.0 - float(np.std(tp_scores)) * 0.8
        conf = min(max(conf, 0.1), 0.99)

        score_100 = round(float(composite) * 100, 2)
        c
