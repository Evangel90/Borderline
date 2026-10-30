"""
gaps/register.py - Policy Gap Register.
Extracts and structures cross-border regulatory gaps identified during incident drills.
"""

import json
import os
from typing import List, Dict, Any
from engine.models import PolicyGap


class GapRegister:
    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        self.gaps_path = os.path.join(run_dir, "gaps.jsonl")
        os.makedirs(run_dir, exist_ok=True)
        self.gaps: List[PolicyGap] = []

    def record_gap(self, gap: PolicyGap) -> None:
        self.gaps.append(gap)
        with open(self.gaps_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(gap.model_dump(), ensure_ascii=False) + "\n")

    def get_summary(self) -> List[Dict[str, Any]]:
        return [g.model_dump() for g in self.gaps]
