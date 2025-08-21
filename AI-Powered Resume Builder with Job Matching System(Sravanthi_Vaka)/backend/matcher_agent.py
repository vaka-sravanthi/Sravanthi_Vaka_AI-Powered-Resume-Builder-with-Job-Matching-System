from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

@dataclass
class MatchDetails:
    resume_chunks: List[str]
    job_chunks: List[str]
    top_pairs: List[Tuple[int, int, float]]  # (resume_idx, job_idx, score)
    overall_similarity: float

class MatcherAgent:
    """
    Embeds resume & job text, indexes with FAISS, and computes similarity.
    Provides explainable top matching chunk pairs.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def _chunk(self, lines: List[str], chunk_size: int = 4) -> List[str]:
        # group sentences into small chunks for better local alignment
        chunks = []
        step = chunk_size
        for i in range(0, len(lines), step):
            chunk = " ".join(lines[i:i+step]).strip()
            if len(chunk) > 15:
                chunks.append(chunk)
        return chunks if chunks else [" ".join(lines)]

    def _embed(self, texts: List[str]) -> np.ndarray:
        embs = self.model.encode(texts, normalize_embeddings=True)
        return np.array(embs, dtype="float32")

    def compute_similarity(self, resume_bullets: List[str], job_bullets: List[str]) -> MatchDetails:
        R = self._chunk(resume_bullets, chunk_size=4)
        J = self._chunk(job_bullets, chunk_size=3)

        R_emb = self._embed(R)
        J_emb = self._embed(J)

        # Build FAISS index for job chunks
        index = faiss.IndexFlatIP(J_emb.shape[1])  # cosine (since normalized)
        index.add(J_emb)

        # For each resume chunk, get best job chunk
        sims = []
        pairs: List[Tuple[int, int, float]] = []
        for i, r in enumerate(R_emb):
            D, I = index.search(r.reshape(1, -1), k=1)
            score = float(D[0][0])
            j = int(I[0][0])
            sims.append(score)
            pairs.append((i, j, score))

        overall = float(np.mean(sims)) if sims else 0.0
        pairs_sorted = sorted(pairs, key=lambda x: x[2], reverse=True)[:5]  # top 5 explanations

        return MatchDetails(resume_chunks=R, job_chunks=J, t
