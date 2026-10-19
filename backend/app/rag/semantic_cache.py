"""
Entitlement-Aware Semantic Cache for Project Atlas.
Provides:
- Sub-50ms cache hits for semantically identical and paraphrased queries.
- Strict client entitlement isolation (client C-02 cannot access cached responses from C-01).
- Blended semantic similarity + keyword overlap threshold matching (default >= 0.82).
- Cost & latency observability metrics.
"""

import time
import logging
from typing import Optional, Dict, Any, List, Set
from app.rag.embeddings import get_embedding_pipeline

logger = logging.getLogger(__name__)

STOPWORDS = {"what", "was", "the", "in", "is", "for", "tell", "me", "a", "an", "and", "or", "to", "of"}

def extract_content_keywords(text: str) -> Set[str]:
    words = text.lower().replace("?", "").replace(".", "").split()
    return {w for w in words if w not in STOPWORDS and len(w) > 1}

class SemanticCacheEntry:
    def __init__(self, client_id: str, query: str, embedding: List[float], response: Dict[str, Any]):
        self.client_id = client_id
        self.query = query
        self.keywords = extract_content_keywords(query)
        self.embedding = embedding
        self.response = response
        self.timestamp = time.time()
        self.hit_count = 0

class EntitlementAwareSemanticCache:
    def __init__(self, similarity_threshold: float = 0.82):
        self.threshold = similarity_threshold
        self.pipeline = get_embedding_pipeline()
        # Key: client_id -> list of SemanticCacheEntry
        self._cache_store: Dict[str, List[SemanticCacheEntry]] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "saved_tokens_approx": 0
        }

    def compute_match_score(self, query: str, query_emb: List[float], entry: SemanticCacheEntry) -> float:
        """Computes blended score using cosine embedding similarity and keyword Jaccard overlap"""
        cosine_sim = self.pipeline.cosine_similarity(query_emb, entry.embedding)
        
        # Keyword Jaccard
        q_kw = extract_content_keywords(query)
        if q_kw and entry.keywords:
            intersection = len(q_kw.intersection(entry.keywords))
            union = len(q_kw.union(entry.keywords))
            jaccard = intersection / union if union > 0 else 0.0
        else:
            jaccard = 0.0

        # Exact keyword match gives strong boost
        if q_kw == entry.keywords:
            return max(cosine_sim, 0.98)

        blended = 0.60 * cosine_sim + 0.40 * jaccard
        return round(blended, 4)

    def get(self, client_id: str, query: str) -> Optional[Dict[str, Any]]:
        """
        Looks up query in semantic cache for the specific client_id.
        Returns cached response if match score >= threshold, else None.
        """
        client_entries = self._cache_store.get(client_id, [])
        if not client_entries:
            self.stats["misses"] += 1
            return None

        query_emb = self.pipeline.embed_text(query)

        best_score = 0.0
        best_entry = None

        for entry in client_entries:
            score = self.compute_match_score(query, query_emb, entry)
            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry and best_score >= self.threshold:
            self.stats["hits"] += 1
            best_entry.hit_count += 1
            
            # Approximate token savings (~4 tokens per word)
            token_savings = int(len(best_entry.response.get("answer", "")) / 4) + 150
            self.stats["saved_tokens_approx"] += token_savings

            logger.info(f"Semantic Cache HIT! Client: {client_id} | Score: {best_score:.4f} | Query: '{query}'")
            
            # Return clone of cached response with cache telemetry
            cached_res = dict(best_entry.response)
            cached_res["cached"] = True
            cached_res["cache_similarity"] = round(best_score, 4)
            cached_res["cached_from_query"] = best_entry.query
            return cached_res

        self.stats["misses"] += 1
        return None

    def put(self, client_id: str, query: str, response: Dict[str, Any]):
        """Caches response under the specific client's partition"""
        if not response.get("answer") or "Error" in response.get("answer", ""):
            return

        if client_id not in self._cache_store:
            self._cache_store[client_id] = []

        query_emb = self.pipeline.embed_text(query)
        entry = SemanticCacheEntry(
            client_id=client_id,
            query=query,
            embedding=query_emb,
            response=response
        )
        self._cache_store[client_id].append(entry)
        logger.info(f"Cached response for Client: {client_id} | Total entries: {len(self._cache_store[client_id])}")

    def get_stats(self) -> Dict[str, Any]:
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_ratio = (self.stats["hits"] / total_requests * 100.0) if total_requests > 0 else 0.0
        return {
            "total_entries": sum(len(v) for v in self._cache_store.values()),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_ratio_percentage": round(hit_ratio, 2),
            "estimated_tokens_saved": self.stats["saved_tokens_approx"]
        }

# Global singleton
_semantic_cache = None

def get_semantic_cache() -> EntitlementAwareSemanticCache:
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = EntitlementAwareSemanticCache()
    return _semantic_cache
