#!/usr/bin/env python3
"""
scripts/run_drill.py - CLI runner for Borderline incident drills.
"""

import argparse
import sys
import time
from engine.orchestrator import DrillOrchestrator
from engine.llm import OllamaError


def main():
    parser = argparse.ArgumentParser(description="Run a cross-border AI incident drill.")
    parser.add_argument("--intent", default="retinopathy-ae-ch", help="Intent filename (without extension)")
    parser.add_argument("--run-id", default=None, help="Custom run identifier")
    args = parser.parse_args()

    intent_file = f"intents/{args.intent}.yaml"
    run_id = args.run_id or f"{args.intent}-{int(time.time())}"

    try:
        orchestrator = DrillOrchestrator(intent_path=intent_file, run_id=run_id)
        orchestrator.run()
    except (OllamaError, ValueError) as exc:
        parser.exit(2, f"LLM runtime error: {exc}\n")


if __name__ == "__main__":
    main()
