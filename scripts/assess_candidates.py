#!/usr/bin/env python3
"""
Apply the evidence-sufficiency rule to gaps/candidate_register.yaml.

Writes report/candidate-status.json and prints one line per candidate. A candidate is
SUPPORTED_CANDIDATE only when all quotes verify, its search records exist and confirm the
absences it relies on, a GLOBAL comparator is quoted, and no obtainable known-missing document
could refute it. Exit code is 1 if the register itself has problems (e.g. a quote fails),
so a broken register cannot pass silently; open candidates alone do not fail.
"""

import argparse
import json
import sys

sys.path.insert(0, ".")

from gaps.sufficiency import SUPPORTED, assess_register, load_chunks, load_register  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--register", default="gaps/candidate_register.yaml")
    parser.add_argument("--out", default="report/candidate-status.json")
    args = parser.parse_args()

    result = assess_register(load_register(args.register), load_chunks())
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    broken = False
    for candidate in result["candidates"]:
        print(f"{candidate['candidate_id']}: {candidate['status']} - {candidate['title']}")
        for unmet in candidate["unmet_conditions"]:
            print(f"    unmet ({unmet['condition']}): {unmet['detail']}")
            # A failed quote or a bad search record means the register is wrong, not just open.
            broken |= unmet["condition"] in {"quotes_verify", "search_record"}
    for problem in result["register_problems"]:
        print(f"register problem: {problem}")
        broken = True
    supported = sum(c["status"] == SUPPORTED for c in result["candidates"])
    print(f"{supported} of {len(result['candidates'])} candidates supported (unreviewed; not legal conclusions). "
          f"Wrote {args.out}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
