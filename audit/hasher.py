"""
audit/hasher.py - Hash-chained audit logger and cryptographic verifier.
"""

import hashlib
import json
import os
from typing import List, Dict, Any, Tuple


class HashChainedLogger:
    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        self.log_path = os.path.join(run_dir, "log.jsonl")
        os.makedirs(run_dir, exist_ok=True)
        self.entries = []
        self.latest_hash = "0" * 64

    def compute_hash(self, prev_hash: str, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        content = f"{prev_hash}:{serialized}".encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def append(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        prev_hash = self.latest_hash
        record_for_hashing = {k: v for k, v in entry.items() if k not in ["prev_hash", "current_hash"]}
        curr_hash = self.compute_hash(prev_hash, record_for_hashing)

        chained_entry = dict(entry)
        chained_entry["prev_hash"] = prev_hash
        chained_entry["current_hash"] = curr_hash

        self.entries.append(chained_entry)
        self.latest_hash = curr_hash

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(chained_entry, ensure_ascii=False) + "\n")

        return chained_entry

    @staticmethod
    def verify_log(log_path: str) -> Tuple[bool, str, int]:
        """
        Verify the integrity of a hash-chained log file.
        Returns: (is_valid: bool, message: str, broken_index: int)
        """
        if not os.path.exists(log_path):
            return False, f"File not found: {log_path}", -1

        expected_prev = "0" * 64
        with open(log_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                prev_hash = record.get("prev_hash")
                current_hash = record.get("current_hash")

                if prev_hash != expected_prev:
                    return False, f"Broken chain at entry {idx}: expected prev_hash {expected_prev}, got {prev_hash}", idx

                # Recompute hash
                clean_payload = {k: v for k, v in record.items() if k not in ["prev_hash", "current_hash"]}
                serialized = json.dumps(clean_payload, sort_keys=True, ensure_ascii=False)
                expected_curr = hashlib.sha256(f"{prev_hash}:{serialized}".encode("utf-8")).hexdigest()

                if current_hash != expected_curr:
                    return False, f"Hash mismatch at entry {idx}: expected {expected_curr}, got {current_hash}", idx

                expected_prev = current_hash

        return True, "All entries in hash chain verified successfully", -1
