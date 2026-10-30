#!/usr/bin/env python3
"""
scripts/run_drill.py - CLI runner for Borderline incident drills.
"""

import argparse
import sys
import time
from engine.orchestrator import DrillOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Run a cross-border AI incident drill.")
    parser.add_argument("--intent", default="retinopathy-ae-ch", help="Intent filename (without extension)")
    parser.add_argument("--run-id", default=None, help="Custom run identifier")
    args = parser.parse_args()

    intent_file = f"intents/{args.intent}.yaml"
    run_id = args.run_id or f"{args.intent}-{int(time.time())}"

    orchestrator = DrillOrchestrator(intent_path=intent_file, run_id=run_id)
    orchestrator.run()


if __name__ == "__main__":
    main()
