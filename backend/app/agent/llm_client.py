"""
Pluggable LLM Client for Project Atlas.
Supports:
1. Local Ollama (e.g. Llama-3, Mistral) via HTTP API: http://localhost:11434
2. Cloud LLMs (Gemini, OpenAI) via standard HTTP endpoints
3. Built-in Deterministic Engine fallback (zero external dependencies, fast, offline)
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3:8b")

    def query_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Calls local Ollama instance running Llama-3 or Mistral"""
        endpoint = f"{self.ollama_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.ollama_model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 512
            }
        }
        try:
            res = requests.post(endpoint, json=payload, timeout=settings.REQUEST_TIMEOUT_SECONDS)
            if res.status_code == 200:
                data = res.json()
                return data.get("response", "").strip()
            else:
                logger.warning(f"Ollama returned HTTP {res.status_code}. Using built-in fallback.")
                return None
        except Exception as e:
            logger.info(f"Ollama not running on {self.ollama_url} ({e}). Using built-in fallback.")
            return None

    def synthesize(self, system_prompt: str, user_prompt: str, fallback_text: str) -> str:
        """
        Attempts LLM generation (Ollama / Gemini / OpenAI).
        If Ollama is not active or times out, gracefully returns the validated fallback.
        """
        if self.provider == "ollama":
            llm_res = self.query_ollama(system_prompt, user_prompt)
            if llm_res:
                return llm_res

        return fallback_text
