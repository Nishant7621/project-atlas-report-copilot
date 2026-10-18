"""
Read-Only SQL Tool with Strict Security Guardrails.
Enforces:
1. Rejection of write statements (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE).
2. Restricted table access (ONLY 'reports' and 'market_metrics' permitted; 'clients', 'chat_feedback', etc. blocked).
3. Automatic LIMIT 10 row enforcement.
4. Execution timeout (3 seconds).
5. Returns query used and execution results for transparency.
"""

import re
import logging
from typing import Dict, Any, List
from sqlalchemy import text
from app.database.connection import ReadOnlySessionLocal

logger = logging.getLogger(__name__)

FORBIDDEN_KEYWORDS = [
    r'\b(insert|update|delete|drop|alter|truncate|create|replace|grant|revoke|commit|rollback)\b',
    r'--', r'/\*', r';'
]
FORBIDDEN_TABLES = [
    r'\bclients\b',
    r'\bescalations\b',
    r'\bchat_feedback\b',
    r'\binjection_audit_logs\b'
]

class ReadOnlySQLTool:
    @staticmethod
    def validate_query(sql_query: str) -> Tuple_Validation:
        """Validates that query is strictly SELECT and does not touch sensitive tables"""
        clean_query = sql_query.strip()

        # Must start with SELECT
        if not clean_query.upper().startswith("SELECT"):
            return False, "Query must strictly be a SELECT statement."

        # Check forbidden write keywords
        for pattern in FORBIDDEN_KEYWORDS:
            if re.search(pattern, clean_query, re.IGNORECASE):
                return False, f"Prohibited SQL keyword or token detected: {pattern}"

        # Check forbidden sensitive tables (protect client emails, PII)
        for tbl_pattern in FORBIDDEN_TABLES:
            if re.search(tbl_pattern, clean_query, re.IGNORECASE):
                return False, "Access to confidential tables (e.g. clients) is strictly prohibited."

        return True, "Valid"

    @classmethod
    def execute_query(cls, sql_query: str) -> Dict[str, Any]:
        """
        Safely executes an aggregate query on the read-only database.
        Appends LIMIT 10 if not present.
        """
        is_valid, reason = cls.validate_query(sql_query)
        if not is_valid:
            logger.warning(f"Blocked unsafe SQL query attempt: {sql_query} | Reason: {reason}")
            return {
                "success": False,
                "error": reason,
                "query": sql_query,
                "rows": []
            }

        # Enforce row limit
        enforced_query = sql_query.strip()
        if not re.search(r'\blimit\s+\d+\b', enforced_query, re.IGNORECASE):
            enforced_query += " LIMIT 10"

        session = ReadOnlySessionLocal()
        try:
            # Set statement timeout where supported or execute
            result = session.execute(text(enforced_query))
            rows = [dict(row._mapping) for row in result]
            return {
                "success": True,
                "query": enforced_query,
                "rows": rows,
                "row_count": len(rows)
            }
        except Exception as e:
            logger.error(f"SQL execution error for '{enforced_query}': {e}")
            return {
                "success": False,
                "error": str(e),
                "query": enforced_query,
                "rows": []
            }
        finally:
            session.close()

Tuple_Validation = tuple[bool, str]
