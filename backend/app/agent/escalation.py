"""
Escalation Manager for Project Atlas.
Creates support/analyst review tickets in MySQL whenever:
- Confidence score drops below threshold
- Forecast questions exceed documented forecast bounds (e.g. 2035)
- User explicitly requests escalation or human analyst intervention
"""

import logging
from typing import Dict, Any, Optional
from app.database.connection import SessionLocal
from app.database.models import Escalation

logger = logging.getLogger(__name__)

class EscalationManager:
    @staticmethod
    def create_escalation_ticket(
        client_id: str,
        question: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Persists a new ticket into the escalations table.
        """
        session = SessionLocal()
        try:
            ticket = Escalation(
                client_id=client_id,
                question=question,
                reason=reason,
                status="open"
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            logger.info(f"Escalation ticket #{ticket.id} created for Client {client_id}: {reason}")
            return {
                "escalated": True,
                "ticket_id": ticket.id,
                "status": "open",
                "reason": reason
            }
        except Exception as e:
            logger.error(f"Failed to create escalation ticket: {e}")
            session.rollback()
            return {
                "escalated": True,
                "ticket_id": None,
                "status": "error",
                "reason": str(e)
            }
        finally:
            session.close()

    @staticmethod
    def get_all_escalations() -> list:
        session = SessionLocal()
        try:
            tickets = session.query(Escalation).order_by(Escalation.created_at.desc()).all()
            return [
                {
                    "id": t.id,
                    "client_id": t.client_id,
                    "question": t.question,
                    "reason": t.reason,
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in tickets
            ]
        finally:
            session.close()
