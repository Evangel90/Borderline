#!/usr/bin/env python3
"""
Verify SHA-256 checksums of all tracked source documents in data/sources.csv
"""
import csv
import hashlib
import os
import sys

def verify_sources(csv_path="data/sources.csv"):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        sys.exit(1)

    all_passed = True
    checked_count = 0

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get("doc_id")
            rel_file = row.get("file")
            expected_sha = row.get("sha256", "").strip()

            if not rel_file:
                continue

            checked_count += 1
            if not os.path.exists(rel_file):
                print(f"❌ [MISSING] {doc_id}: file not found at '{rel_file}'")
                all_passed = False
                continue

            with open(rel_file, "rb") as file_to_check:
                actual_sha = hashlib.sha256(file_to_check.read()).hexdigest()

            if not expected_sha:
                print(f"⚠️  [NO HASH] {doc_id}: '{rel_file}' has no recorded SHA-256")
                all_passed = False
            elif actual_sha.lower() != expected_sha.lower():
                print(f"❌ [MISMATCH] {doc_id}: expected {expected_sha[:10]}..., got {actual_sha[:10]}...")
                all_passed = False
            else:
                print(f"✅ [OK] {doc_id} -> {rel_file}")

            extraction_file = (row.get("extraction_file") or "").strip()
            extraction_sha = (row.get("extraction_sha256") or "").strip()
            if extraction_file:
                checked_count += 1
                if not os.path.exists(extraction_file):
                    print(f"❌ [MISSING OCR] {doc_id}: file not found at '{extraction_file}'")
                    all_passed = False
                else:
                    with open(extraction_file, "rb") as derived:
                        actual_extraction_sha = hashlib.sha256(derived.read()).hexdigest()
                    if not extraction_sha:
                        print(f"⚠️  [NO OCR HASH] {doc_id}: '{extraction_file}' has no SHA-256")
                        all_passed = False
                    elif actual_extraction_sha.lower() != extraction_sha.lower():
                        print(
                            f"❌ [OCR MISMATCH] {doc_id}: expected "
                            f"{extraction_sha[:10]}..., got {actual_extraction_sha[:10]}..."
                        )
                        all_passed = False
                    else:
                        print(f"✅ [OK OCR] {doc_id} -> {extraction_file}")

    print("-" * 50)
    if all_passed:
        print(f"All {checked_count} tracked source and extraction artifacts verified successfully!")
        return 0
    else:
        print(f"Verification failed on one or more documents.")
        return 1

if __name__ == "__main__":
    sys.exit(verify_sources())
