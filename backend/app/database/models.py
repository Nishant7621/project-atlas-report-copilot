"""
SQLAlchemy models for Project Atlas:
- reports
- market_metrics
- clients
- escalations
- chat_feedback
- injection_audit_logs
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(20), primary_key=True)  # e.g. 'R-101'
    title = Column(String(255), nullable=False)
    publisher = Column(String(100), nullable=False)
    published = Column(Date, nullable=False)
    sector = Column(String(100), nullable=False)
    access = Column(String(50), nullable=False)  # 'paid', 'public excerpt'

    metrics = relationship("MarketMetric", back_populates="report", cascade="all, delete-orphan")

class MarketMetric(Base):
    __tablename__ = "market_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(20), ForeignKey("reports.id"), nullable=False)
    metric = Column(String(100), nullable=False)       # 'Market size', 'CAGR', 'Regional share'
    region = Column(String(100), nullable=False)       # 'Global', 'APAC'
    year_period = Column(String(50), nullable=False)   # '2024', '2025-2030'
    value = Column(String(100), nullable=False)        # 'USD 4.21 B', '11.2 %'
    scope_note = Column(Text, nullable=True)

    report = relationship("Report", back_populates="metrics")

class Client(Base):
    __tablename__ = "clients"

    id = Column(String(20), primary_key=True)          # 'C-01', 'C-02'
    company = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False) # confidential
    purchased_reports = Column(Text, nullable=False)    # comma-separated: 'R-101, R-103'

class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(20), nullable=False)
    question = Column(Text, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(20), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    rating = Column(String(10), nullable=False)        # 'up', 'down'
    created_at = Column(DateTime, default=datetime.utcnow)

class InjectionAuditLog(Base):
    __tablename__ = "injection_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(20), nullable=False)
    source_report = Column(String(50), nullable=True)
    snippet = Column(Text, nullable=False)
    detected_rule = Column(String(100), nullable=False)
    flagged_at = Column(DateTime, default=datetime.utcnow)
