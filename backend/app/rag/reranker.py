"""
Cross-Encoder Semantic Re-Ranker for Project Atlas.
Implements Stage 2 of the Two-Stage Retrieval Pipeline:
Takes Top 15 candidate chunks from first-stage retrieval and computes fine-grained
cross-interaction scores between query and document text.
"""

import re
import logging
from typing import List, Dict, Any
from app.rag.embeddings import get_embedding_pipeline

logger = logging.getLogger(__name__)

class CrossEncoderReRanker:
    def __init__(self):
        self.pipeline = get_embedding_pipeline()

    def score_pair(self, query: str, chunk: Dict[str, Any]) -> float:
        """
        Calculates cross-interaction score:
        1. Dense semantic vector similarity between query and chunk text
        2. Exact keyword / phrase co-occurrence density
        3. Quantitative figure proximity boost (numbers, dollar signs, percentages)
        4. Explicit metadata alignment boost (matching report_id or page requested in query)
        """
        chunk_text = chunk.get("text", "")
        q_emb = self.pipeline.embed_text(query)
        d_emb = self.pipeline.embed_text(chunk_text)
        semantic_sim = self.pipeline.cosine_similarity(q_emb, d_emb)

        q_lower = query.lower()
        q_words = set(q_lower.split())
        d_words = chunk_text.lower().split()
        
        # Word overlap ratio
        overlap_count = sum(1 for w in q_words if w in d_words)
        lexical_density = overlap_count / max(1, len(q_words))

        # Financial figure affinity
        has_figures = any(term in chunk_text.lower() for term in ["usd", "$", "billion", "%", "cagr"])
        figure_boost = 1.20 if has_figures else 1.0

        # Exact metadata alignment boost (e.g. user asked for R-102, or page 14)
        meta_boost = 1.0
        rep_id = chunk.get("report_id", "").lower()
        if rep_id and rep_id in q_lower:
            meta_boost *= 1.6
        
        page_num = str(chunk.get("page", ""))
        if page_num and (f"page {page_num}" in q_lower or f"p{page_num}" in q_lower):
            meta_boost *= 1.4

        # Blended cross-encoder score
        base_score = (0.50 * semantic_sim + 0.50 * lexical_density) * figure_boost
        final_score = base_score * meta_boost
        return round(final_score, 4)

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Re-ranks candidate chunks and returns the top_k most relevant ones.
        """
        if not candidate_chunks:
            return []

        scored_candidates = []
        for chunk in candidate_chunks:
            cross_score = self.score_pair(query, chunk)
            c = dict(chunk)
            c["rerank_score"] = cross_score
            scored_candidates.append(c)

        # Sort descending by rerank_score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_k]

# Global singleton
_reranker = None

def get_reranker() -> CrossEncoderReRanker:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReRanker()
    return _reranker
