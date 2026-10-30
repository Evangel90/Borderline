#!/usr/bin/env python3
"""
scripts/verify_log.py - Verify cryptographic integrity of the hash-chained run log.
"""

import argparse
import sys
from audit.hasher import HashChainedLogger


def main():
    parser = argparse.ArgumentParser(description="Verify hash chain integrity of a drill run.")
    parser.add_argument("--run", required=True, help="Run ID to verify")
    args = parser.parse_args()

    log_file = f"runs/{args.run}/log.jsonl"
    print(f"🔍 Verifying hash chain in {log_file}...")

    is_valid, msg, broken_idx = HashChainedLogger.verify_log(log_file)
    if is_valid:
        print(f"✅ {msg}")
        sys.exit(0)
    else:
        print(f"❌ Verification failed: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
