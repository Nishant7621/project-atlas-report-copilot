"""
Seed database with required seed data from Appendix A + expanded synthetic reports.
"""

from datetime import datetime
from app.database.connection import SessionLocal, init_db
from app.database.models import Report, MarketMetric, Client

def seed_database():
    init_db()
    session = SessionLocal()
    try:
        # Check if already seeded
        if session.query(Report).count() > 0:
            print("Database already contains data. Skipping re-seed.")
            return

        # 1. Reports
        reports_data = [
            Report(
                id="R-101",
                title="Global Smart Water Meter Market 2025",
                publisher="CMR",
                published=datetime.strptime("2025-03-10", "%Y-%m-%d").date(),
                sector="Utilities",
                access="paid"
            ),
            Report(
                id="R-102",
                title="Smart Water Metering: Industry Outlook 2024",
                publisher="Aquila Insights (third party)",
                published=datetime.strptime("2024-06-18", "%Y-%m-%d").date(),
                sector="Utilities",
                access="public excerpt"
            ),
            Report(
                id="R-103",
                title="Residential Water Purifier Market 2025",
                publisher="CMR",
                published=datetime.strptime("2025-01-22", "%Y-%m-%d").date(),
                sector="Consumer Durables",
                access="paid"
            ),
            Report(
                id="R-104",
                title="Electric Vehicle Charging Infrastructure Outlook 2025",
                publisher="CMR",
                published=datetime.strptime("2025-02-14", "%Y-%m-%d").date(),
                sector="Automotive & Energy",
                access="paid"
            ),
            Report(
                id="R-105",
                title="Healthcare AI Diagnostics and Imaging Market 2025",
                publisher="CMR",
                published=datetime.strptime("2025-03-01", "%Y-%m-%d").date(),
                sector="Healthcare & Life Sciences",
                access="paid"
            ),
            Report(
                id="R-106",
                title="Commercial Battery Energy Storage Systems (BESS) 2025",
                publisher="CMR",
                published=datetime.strptime("2025-02-28", "%Y-%m-%d").date(),
                sector="Utilities & Clean Tech",
                access="paid"
            )
        ]
        session.add_all(reports_data)
        session.commit()

        # 2. Market Metrics
        metrics_data = [
            # R-101
            MarketMetric(
                report_id="R-101",
                metric="Market size",
                region="Global",
                year_period="2024",
                value="USD 4.21 B",
                scope_note="Includes hardware, software and services"
            ),
            MarketMetric(
                report_id="R-101",
                metric="CAGR",
                region="Global",
                year_period="2025-2030",
                value="11.2 %",
                scope_note="Forecast period stated as 2025-2030"
            ),
            MarketMetric(
                report_id="R-101",
                metric="Regional share",
                region="APAC",
                year_period="2024",
                value="38 %",
                scope_note="Share of global market size"
            ),

            # R-102
            MarketMetric(
                report_id="R-102",
                metric="Market size",
                region="Global",
                year_period="2024",
                value="USD 3.87 B",
                scope_note="AMR / AMI hardware only"
            ),
            MarketMetric(
                report_id="R-102",
                metric="CAGR",
                region="Global",
                year_period="2024-2029",
                value="9.8 %",
                scope_note="Different forecast window from R-101"
            ),
            MarketMetric(
                report_id="R-102",
                metric="Regional share",
                region="APAC",
                year_period="2024",
                value="41 %",
                scope_note="Share of hardware market"
            ),

            # R-103
            MarketMetric(
                report_id="R-103",
                metric="Market size",
                region="Global",
                year_period="2024",
                value="USD 9.54 B",
                scope_note="Point-of-use residential filtration systems"
            ),
            MarketMetric(
                report_id="R-103",
                metric="CAGR",
                region="Global",
                year_period="2025-2030",
                value="8.7 %",
                scope_note="Reverse osmosis and UV technology focus"
            ),
            MarketMetric(
                report_id="R-103",
                metric="Regional share",
                region="APAC",
                year_period="2024",
                value="44 %",
                scope_note="Driven by municipal water quality issues"
            ),

            # R-104
            MarketMetric(
                report_id="R-104",
                metric="Market size",
                region="Global",
                year_period="2024",
                value="USD 18.60 B",
                scope_note="AC Level 2 and DC Fast Charging equipment"
            ),
            MarketMetric(
                report_id="R-104",
                metric="CAGR",
                region="Global",
                year_period="2025-2030",
                value="24.3 %",
                scope_note="Rapid commercial and public corridor rollout"
            ),

            # R-105
            MarketMetric(
                report_id="R-105",
                metric="Market size",
                region="Global",
                year_period="2024",
                value="USD 2.85 B",
                scope_note="Clinical AI decision support and imaging"
            ),
            MarketMetric(
                report_id="R-105",
                metric="CAGR",
                region="Global",
                year_period="2025-2030",
                value="28.1 %",
                scope_note="FDA and CE cleared diagnostic algorithms"
            ),

            # R-106
            MarketMetric(
                report_id="R-106",
                metric="Market size",
                region="Global",
                year_period="2024",
                value="USD 7.12 B",
                scope_note="Stationary commercial electrochemical storage"
            ),
            MarketMetric(
                report_id="R-106",
                metric="CAGR",
                region="Global",
                year_period="2025-2030",
                value="16.5 %",
                scope_note="Lithium iron phosphate battery installations"
            )
        ]
        session.add_all(metrics_data)

        # 3. Clients
        clients_data = [
            Client(
                id="C-01",
                company="Northwind Utilities",
                contact_email="ops@example.com",
                purchased_reports="R-101, R-103"
            ),
            Client(
                id="C-02",
                company="Blue Delta Infra",
                contact_email="procurement@example.com",
                purchased_reports="R-103"
            )
        ]
        session.add_all(clients_data)

        session.commit()
        print("Successfully seeded Project Atlas database with Appendix A tables and records.")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
