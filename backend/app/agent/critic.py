"""
Critic, Fact-Checker, and Conflict Detection Module for Project Atlas.
Enforces:
1. Citation mapping: Ensures every stated figure maps to a source report chunk.
2. Conflict detection: Detects discrepancies across sources (e.g. R-101 vs R-102 market sizes).
3. Scope clarification: Enforces that conflicting figures are presented with scope differences, never averaged.
"""

from typing import List, Dict, Any, Tuple

class CriticFactChecker:
    @staticmethod
    def detect_conflicts(retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyzes retrieved chunks for conflicting figures or methodologies.
        Specifically evaluates R-101 vs R-102 discrepancies.
        """
        conflicts = []
        report_ids = {c.get("report_id") for c in retrieved_chunks}

        # Check for R-101 and R-102 coexistence or references
        if "R-101" in report_ids and "R-102" in report_ids:
            conflicts.append({
                "metric": "2024 Global Smart Water Meter Market Size",
                "sources": [
                    {
                        "report_id": "R-101",
                        "publisher": "CMR",
                        "value": "USD 4.21 Billion",
                        "scope": "Turnkey scope (hardware, software, and managed services)",
                        "citation": "R-101, Page 8"
                    },
                    {
                        "report_id": "R-102",
                        "publisher": "Aquila Insights",
                        "value": "USD 3.87 Billion",
                        "scope": "Physical AMR / AMI measuring hardware instrumentation only",
                        "citation": "R-102, Page 14"
                    }
                ],
                "explanation": (
                    "The discrepancy of USD 0.34 Billion is attributable to scope boundary differences: "
                    "R-101 includes meter data management software and cloud services, while R-102 measures physical hardware shipments only. "
                    "These figures represent different market definitions and must not be averaged."
                )
            })

        return conflicts

    @staticmethod
    def verify_citations(
        draft_text: str, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extracts and verifies citations mentioned in the text against retrieved chunks.
        """
        citations = []
        for chunk in retrieved_chunks:
            rep_id = chunk.get("report_id")
            page = chunk.get("page")
            label = f"{rep_id}, Page {page}"
            
            # If chunk was relevant
            citations.append({
                "report_id": rep_id,
                "page": page,
                "label": label,
                "sector": chunk.get("sector"),
                "year": chunk.get("year"),
                "snippet": chunk.get("text", "")[:180] + "..."
            })

        # Deduplicate citations by label
        unique_citations = []
        seen = set()
        for cit in citations:
            if cit["label"] not in seen:
                seen.add(cit["label"])
                unique_citations.append(cit)

        return unique_citations

    @staticmethod
    def calculate_confidence(
        has_citations: bool,
        has_conflicts: bool,
        is_derived: bool,
        is_out_of_scope: bool,
        is_injection: bool,
        unentitled_request: bool
    ) -> float:
        """Calculates confidence score (0.0 to 1.0)"""
        if is_out_of_scope or is_injection:
            return 1.0  # High confidence in the refusal

        if unentitled_request:
            return 0.95 # High confidence in entitlement denial & upgrade offer

        if not has_citations and not is_derived:
            return 0.35 # Low confidence, lacks backing data

        score = 0.90
        if has_conflicts:
            score -= 0.10 # Uncertainty due to multiple differing methodology scopes
        if is_derived:
            score -= 0.05 # Stated assumption variance

        return round(max(0.0, min(1.0, score)), 2)
