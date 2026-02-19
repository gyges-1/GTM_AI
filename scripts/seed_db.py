#!/usr/bin/env python3
"""
Seed the database with sample GTM data for development/testing.

Usage:
    python scripts/seed_db.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from backend.db.session import AsyncSessionLocal, async_engine
from backend.db.models import Base


async def create_sample_tables(conn) -> None:
    """Create sample domain tables for GTM analytics."""
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            email TEXT,
            company TEXT,
            lead_source TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS closed_deals (
            id SERIAL PRIMARY KEY,
            deal_name TEXT,
            amount NUMERIC,
            outcome TEXT,  -- 'won' | 'lost'
            close_date DATE,
            stage TEXT,
            owner_id TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS renewals (
            id SERIAL PRIMARY KEY,
            account_id TEXT,
            account_name TEXT,
            contract_value NUMERIC,
            renewal_date DATE,
            health_score NUMERIC,
            csm_owner TEXT,
            contract_type TEXT DEFAULT 'annual',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))


async def seed_leads(conn) -> None:
    sources = ["organic", "paid_search", "referral", "outbound", "event", "partner"]
    statuses = ["new", "qualified", "converted", "disqualified"]
    leads = []
    for i in range(1, 201):
        source = sources[i % len(sources)]
        status = statuses[i % len(statuses)]
        leads.append({
            "email": f"lead{i}@example.com",
            "company": f"Company {i}",
            "lead_source": source,
            "status": status,
        })

    for lead in leads:
        await conn.execute(
            text("INSERT INTO leads (email, company, lead_source, status) VALUES (:email, :company, :lead_source, :status) ON CONFLICT DO NOTHING"),
            lead,
        )
    print(f"  Seeded {len(leads)} leads")


async def seed_closed_deals(conn) -> None:
    import random
    random.seed(42)
    stages = ["Closed Won", "Closed Lost"]
    deals = []
    for i in range(1, 101):
        outcome = "won" if i % 3 != 0 else "lost"
        month = (i % 12) + 1
        deals.append({
            "deal_name": f"Deal {i}",
            "amount": random.choice([5000, 10000, 25000, 50000, 100000]),
            "outcome": outcome,
            "close_date": f"2025-{month:02d}-15",
            "stage": "Closed Won" if outcome == "won" else "Closed Lost",
            "owner_id": f"rep_{i % 5 + 1}",
        })

    for deal in deals:
        await conn.execute(
            text("""
                INSERT INTO closed_deals (deal_name, amount, outcome, close_date, stage, owner_id)
                VALUES (:deal_name, :amount, :outcome, :close_date, :stage, :owner_id)
                ON CONFLICT DO NOTHING
            """),
            deal,
        )
    print(f"  Seeded {len(deals)} closed deals")


async def seed_renewals(conn) -> None:
    renewals = [
        ("acc001", "Acme Corp", 48000, "2025-03-31", 78, "csm_alice", "annual"),
        ("acc002", "Beta Inc", 24000, "2025-02-28", 45, "csm_bob", "annual"),
        ("acc003", "Gamma Ltd", 120000, "2025-04-30", 92, "csm_alice", "multi-year"),
        ("acc004", "Delta LLC", 18000, "2025-03-15", 30, "csm_charlie", "annual"),
        ("acc005", "Epsilon Co", 72000, "2025-05-31", 85, "csm_bob", "annual"),
    ]

    for r in renewals:
        await conn.execute(
            text("""
                INSERT INTO renewals (account_id, account_name, contract_value, renewal_date, health_score, csm_owner, contract_type)
                VALUES (:account_id, :account_name, :contract_value, :renewal_date, :health_score, :csm_owner, :contract_type)
                ON CONFLICT DO NOTHING
            """),
            dict(zip(["account_id", "account_name", "contract_value", "renewal_date", "health_score", "csm_owner", "contract_type"], r)),
        )
    print(f"  Seeded {len(renewals)} renewals")


async def main() -> None:
    print("Seeding database...")

    async with async_engine.begin() as conn:
        # Ensure app tables exist
        await conn.run_sync(Base.metadata.create_all)

        # Create sample domain tables
        await create_sample_tables(conn)

        # Seed data
        await seed_leads(conn)
        await seed_closed_deals(conn)
        await seed_renewals(conn)

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
