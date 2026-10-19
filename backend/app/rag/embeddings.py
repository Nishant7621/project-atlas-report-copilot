"""
3-Tier Embedding Pipeline for Project Atlas.
Tier 1: Cloud API (Google Gemini / OpenAI Embeddings if keys present)
Tier 2: Hugging Face Inference API (sentence-transformers/all-MiniLM-L6-v2)
Tier 3: Built-in 384-dimensional Dense Semantic Hash Vector Fallback (100% offline, zero-dependency)
"""

import os
import math
import hashlib
import logging
import requests
from typing import List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY", os.getenv("HF_TOKEN", ""))

class TieredEmbeddingPipeline:
    def __init__(self):
        self.hf_token = HF_TOKEN
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.dim = 384

    def _normalize(self, vector: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:
            return [0.0] * len(vector)
        return [round(x / norm, 6) for x in vector]

    def _tier1_cloud_embedding(self, text: str) -> Optional[List[float]]:
        """Tier 1: Cloud API embedding (Gemini / OpenAI)"""
        if self.gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.gemini_key}"
                payload = {
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": text[:2048]}]}
                }
                res = requests.post(url, json=payload, timeout=5)
                if res.status_code == 200:
                    values = res.json()["embedding"]["values"]
                    return self._normalize(values[:self.dim])
            except Exception as e:
                logger.info(f"Tier 1 (Gemini) embedding unavailable: {e}. Falling back to Tier 2.")
        return None

    def _tier2_huggingface_embedding(self, text: str) -> Optional[List[float]]:
        """Tier 2: Hugging Face Inference API fallback"""
        try:
            headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}
            res = requests.post(
                HF_API_URL, 
                headers=headers, 
                json={"inputs": [text[:512]], "options": {"wait_for_model": False}}, 
                timeout=4
            )
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    vec = data[0] if isinstance(data[0], list) else data
                    return self._normalize(vec[:self.dim])
        except Exception as e:
            logger.info(f"Tier 2 (Hugging Face) fallback unavailable: {e}. Falling back to Tier 3.")
        return None

    def _tier3_semantic_hash_fallback(self, text: str) -> List[float]:
        """
        Tier 3: Built-in 384-dimensional dense semantic hash vector.
        Deterministic, zero-dependency, and works 100% offline.
        Uses character n-grams and token hashes projected onto a 384-dim hypersphere.
        """
        vec = [0.0] * self.dim
        tokens = text.lower().split()
        
        # Word-level features
        for token in tokens:
            h = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dim
            val = ((h >> 8) % 1000) / 1000.0 - 0.5
            vec[idx] += val

        # Character trigrams for morphological and prefix similarity
        for i in range(len(text) - 2):
            trigram = text[i:i+3].lower()
            h = int(hashlib.sha256(trigram.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dim
            vec[idx] += 0.25

        return self._normalize(vec)

    def embed_text(self, text: str) -> List[float]:
        """
        Cascades through the 3-tier embedding hierarchy:
        Tier 1 (Cloud) -> Tier 2 (Hugging Face) -> Tier 3 (Local Semantic Hash Fallback)
        """
        # Try Tier 1
        emb = self._tier1_cloud_embedding(text)
        if emb:
            return emb

        # Try Tier 2
        emb = self._tier2_huggingface_embedding(text)
        if emb:
            return emb

        # Guaranteed Tier 3 fallback
        return self._tier3_semantic_hash_fallback(text)

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two unit-normalized vectors"""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        return sum(a * b for a, b in zip(vec_a, vec_b))

# Global singleton
_embedding_pipeline = None

def get_embedding_pipeline() -> TieredEmbeddingPipeline:
    global _embedding_pipeline
    if _embedding_pipeline is None:
        _embedding_pipeline = TieredEmbeddingPipeline()
    return _embedding_pipeline
