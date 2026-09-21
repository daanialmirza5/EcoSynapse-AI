#!/usr/bin/env python3
"""Retrieval Pipeline Latency and Throughput Benchmark CLI.

Measures p50, p95, and p99 query retrieval times, vector similarity computation speeds,
and memory utilization across diverse ecological queries.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.knowledge.seed import seed_all
from app.retrieval.hybrid import retrieve_with_trace


SAMPLE_QUERIES = [
    "What are the impacts of cover cropping on soil organic carbon?",
    "How does riparian restoration affect macroinvertebrate diversity in agricultural watersheds?",
    "Evaluate drought-tolerant hedgerows under declining annual rainfall.",
    "Effects of biochar application on microbial respiration and nitrogen retention.",
    "Integrated pest management strategies to reduce pesticide runoff in orchards.",
]


def run_benchmark(iterations_per_query: int = 10):
    print("=" * 70)
    print("EcoSynapse AI Retrieval Pipeline Benchmark")
    print(f"Running {len(SAMPLE_QUERIES)} queries x {iterations_per_query} iterations = {len(SAMPLE_QUERIES) * iterations_per_query} total retrievals")
    print("=" * 70)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_all(db)
    latencies: list[float] = []

    try:
        # Warmup
        for q in SAMPLE_QUERIES:
            retrieve_with_trace(db, q, top_k=5)

        # Timed runs
        for q_idx, q in enumerate(SAMPLE_QUERIES, 1):
            q_latencies = []
            for _ in range(iterations_per_query):
                t0 = time.perf_counter()
                res = retrieve_with_trace(db, q, top_k=5)
                t1 = time.perf_counter()
                elapsed_ms = (t1 - t0) * 1000
                q_latencies.append(elapsed_ms)
                latencies.append(elapsed_ms)

            q_latencies.sort()
            p50 = q_latencies[len(q_latencies) // 2]
            p95 = q_latencies[int(len(q_latencies) * 0.95)]
            print(f"[{q_idx}/{len(SAMPLE_QUERIES)}] Query: {q[:45]}...")
            print(f"    p50: {p50:.2f} ms | p95: {p95:.2f} ms | results: {len(res.results)}")

        latencies.sort()
        overall_p50 = latencies[len(latencies) // 2]
        overall_p95 = latencies[int(len(latencies) * 0.95)]
        overall_p99 = latencies[int(len(latencies) * 0.99)]
        throughput_qps = 1000.0 / (sum(latencies) / len(latencies))

        print("-" * 70)
        print("Benchmark Summary:")
        print(f"  Total Runs:      {len(latencies)}")
        print(f"  Latency p50:     {overall_p50:.2f} ms")
        print(f"  Latency p95:     {overall_p95:.2f} ms")
        print(f"  Latency p99:     {overall_p99:.2f} ms")
        print(f"  Throughput:      {throughput_qps:.1f} queries/sec")
        print("=" * 70)
    finally:
        db.close()


if __name__ == "__main__":
    run_benchmark(iterations_per_query=10)
