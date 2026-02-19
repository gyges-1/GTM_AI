#!/usr/bin/env python3
"""
CLI smoke test for the GTM AI agent system.

Invokes the supervisor with sample GTM questions and validates routing + responses.

Usage:
    python scripts/test_agent.py
    python scripts/test_agent.py --question "What is our pipeline coverage?"
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
from dotenv import load_dotenv
load_dotenv()

SAMPLE_QUESTIONS = [
    {
        "question": "What's our current pipeline coverage ratio?",
        "expected_agent": "pipeline_management",
    },
    {
        "question": "Give me a Q2 revenue forecast based on current opportunities.",
        "expected_agent": "forecasting",
    },
    {
        "question": "Which accounts are at highest churn risk this quarter?",
        "expected_agent": "customer_success",
    },
    {
        "question": "How are our demand generation campaigns performing this month?",
        "expected_agent": "demand_generation",
    },
    {
        "question": "What are the best growth opportunities in the Enterprise segment?",
        "expected_agent": "growth_intelligence",
    },
]


async def run_test(question: str, expected_agent: str | None = None) -> dict:
    """Run a single test question through the supervisor."""
    from langchain_core.messages import HumanMessage

    print(f"\n{'='*60}")
    print(f"Question: {question}")
    if expected_agent:
        print(f"Expected agent: {expected_agent}")

    # For smoke test, build a minimal graph without checkpointer persistence
    import psycopg
    from backend.config import get_settings
    from backend.agents.supervisor import build_supervisor_graph

    settings = get_settings()

    # Use a simple in-memory checkpointer for the smoke test
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()

    # Build minimal integrations (only Postgres which is always available)
    integrations: dict = {}
    try:
        from backend.integrations.postgres import PostgresIntegration
        pg = PostgresIntegration(settings)
        await pg.health_check()
        integrations["postgres"] = pg
        print("  Postgres: connected")
    except Exception as e:
        print(f"  Postgres: unavailable ({e})")

    graph = await build_supervisor_graph(checkpointer, integrations)

    thread_id = f"smoke-test-{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    start = time.monotonic()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=question)]},
        config=config,
    )
    elapsed = time.monotonic() - start

    messages = result.get("messages", [])
    last_ai = next(
        (m for m in reversed(messages) if hasattr(m, "type") and m.type == "ai"),
        None,
    )
    response = last_ai.content if last_ai else "No response"
    active_agent = result.get("active_agent")

    print(f"\nResponse ({elapsed:.1f}s):")
    print(f"  Agent: {active_agent or 'unknown'}")
    print(f"  Answer: {str(response)[:300]}{'...' if len(str(response)) > 300 else ''}")

    passed = True
    if expected_agent and active_agent:
        if active_agent != expected_agent:
            print(f"  [WARNING] Expected {expected_agent}, got {active_agent}")
            passed = False
        else:
            print(f"  [PASS] Routed to correct agent")

    return {"question": question, "agent": active_agent, "passed": passed, "elapsed": elapsed}


async def main() -> None:
    parser = argparse.ArgumentParser(description="GTM AI smoke test")
    parser.add_argument("--question", "-q", help="Single question to test")
    args = parser.parse_args()

    if args.question:
        await run_test(args.question)
        return

    print("Running GTM AI Agent smoke tests...")
    results = []

    for test_case in SAMPLE_QUESTIONS:
        try:
            result = await run_test(
                test_case["question"],
                test_case.get("expected_agent"),
            )
            results.append(result)
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append({"question": test_case["question"], "passed": False, "error": str(e)})

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for r in results if r.get("passed", False))
    total = len(results)
    print(f"Passed: {passed}/{total}")
    for r in results:
        status = "✓" if r.get("passed") else "✗"
        agent = r.get("agent", "error")
        elapsed = r.get("elapsed", 0)
        print(f"  {status} [{agent}] {r['question'][:60]} ({elapsed:.1f}s)")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
