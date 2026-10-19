"""
Entitlement-Aware Vector Store for Project Atlas.
Provides:
- Chunk indexing with full metadata.
- Strict entitlement pre-filtering (filtering out unpurchased reports BEFORE ranking or LLM ingestion).
- Stemmed hybrid lexical similarity search with BM25 scoring.
"""

import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from app.database.connection import SessionLocal
from app.database.models import Client, Report

class EntitlementAwareVectorStore:
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir
        self.chunks: List[Dict[str, Any]] = []
        self.doc_freq: Dict[str, int] = {}
        self.total_docs: int = 0

    def stem_token(self, token: str) -> str:
        """Lightweight English suffix normalizer (purifiers -> purifier, meters -> meter)"""
        t = token.lower()
        if t.endswith("ies") and len(t) > 4:
            return t[:-3] + "y"
        if t.endswith("es") and len(t) > 4:
            return t[:-2]
        if t.endswith("s") and not t.endswith("ss") and len(t) > 3:
            return t[:-1]
        if t.endswith("ing") and len(t) > 5:
            return t[:-3]
        return t

    def tokenize(self, text: str) -> List[str]:
        """Tokenizes and stems words for robust information retrieval"""
        raw_tokens = re.findall(r'\b[a-zA-Z0-9_\-\.]+\b', text.lower())
        return [self.stem_token(t) for t in raw_tokens if len(t) > 1]

    def build_index(self, chunks: List[Dict[str, Any]]):
        """Indexes all document chunks and pre-calculates IDF statistics"""
        self.chunks = chunks
        self.total_docs = len(chunks)
        self.doc_freq = {}

        for chunk in chunks:
            tokens = set(self.tokenize(chunk["text"]))
            for t in tokens:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

    def get_allowed_reports(self, client_id: str) -> Set[str]:
        """
        Retrieves the exact list of report IDs that this client is permitted to view:
        1. Explicitly purchased reports in the clients table
        2. Public reports (access == 'public excerpt')
        """
        session = SessionLocal()
        try:
            # 1. Get public reports
            public_reps = session.query(Report.id).filter(Report.access == "public excerpt").all()
            allowed = {r[0] for r in public_reps}

            # 2. Get client purchased reports
            client = session.query(Client).filter(Client.id == client_id).first()
            if client and client.purchased_reports:
                for rep in client.purchased_reports.split(","):
                    allowed.add(rep.strip())

            return allowed
        finally:
            session.close()

    def get_client_entitlement_status(self, client_id: str, target_report_id: str) -> Dict[str, Any]:
        """
        Checks whether client owns target_report_id.
        If not, checks whether the report exists in the catalog so an upgrade offer can be presented.
        """
        allowed = self.get_allowed_reports(client_id)
        has_access = target_report_id in allowed

        session = SessionLocal()
        try:
            report = session.query(Report).filter(Report.id == target_report_id).first()
            exists_in_catalog = report is not None
            report_title = report.title if report else ""
            report_access = report.access if report else ""
            return {
                "has_access": has_access,
                "exists_in_catalog": exists_in_catalog,
                "report_id": target_report_id,
                "title": report_title,
                "access_type": report_access
            }
        finally:
            session.close()

    def search(
        self, 
        query: str, 
        client_id: str, 
        top_k: int = 5,
        target_report_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs entitlement-aware search.
        PRE-FILTER RULE: Chunks from reports the client has not purchased are completely removed
        before any matching or ranking happens.
        """
        allowed_reports = self.get_allowed_reports(client_id)
        query_tokens = self.tokenize(query)

        scored_results = []

        for chunk in self.chunks:
            # STRICT ENTITLEMENT PRE-FILTER:
            if chunk["report_id"] not in allowed_reports:
                continue

            # Optional filter by specific report
            if target_report_id and chunk["report_id"] != target_report_id:
                continue

            chunk_tokens = self.tokenize(chunk["text"])
            if not chunk_tokens:
                continue

            # Lexical BM25-style scoring
            score = 0.0
            chunk_token_counts = {}
            for t in chunk_tokens:
                chunk_token_counts[t] = chunk_token_counts.get(t, 0) + 1

            for qt in query_tokens:
                if qt in chunk_token_counts:
                    tf = chunk_token_counts[qt] / len(chunk_tokens)
                    df = self.doc_freq.get(qt, 1)
                    idf = math.log((self.total_docs + 1) / (df + 1)) + 1.0
                    score += tf * idf * 2.0

            # Boost exact phrases or key acronyms
            text_lower = chunk["text"].lower()
            if any(term in text_lower for term in ["usd", "billion", "cagr", "%"]):
                score *= 1.2

            if score > 0:
                result_chunk = dict(chunk)
                result_chunk["score"] = round(score, 4)
                scored_results.append(result_chunk)

        # Sort descending by candidate score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        candidates = scored_results[:15]  # Stage 1: Candidate Generation (top 15)

        # Stage 2: Cross-Encoder Re-Ranking
        try:
            from app.rag.reranker import get_reranker
            reranker = get_reranker()
            return reranker.rerank(query, candidates, top_k=top_k)
        except Exception:
            return candidates[:top_k]

# Global singleton
_vector_store = None

def get_vector_store(force_refresh: bool = False) -> EntitlementAwareVectorStore:
    global _vector_store
    if _vector_store is None or force_refresh:
        from app.rag.chunker import ReportChunker
        from app.config import settings
        chunker = ReportChunker(settings.REPORTS_DIR)
        chunks = chunker.chunk_all_reports()
        _vector_store = EntitlementAwareVectorStore(settings.VECTOR_DB_DIR)
        _vector_store.build_index(chunks)
    return _vector_store
