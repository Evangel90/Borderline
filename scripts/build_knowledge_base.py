"""Build the Borderline knowledge base in the ITU AI Readiness reference-code layout.

The knowledge base lives in knowledge-base/:

    knowledge-base/
      InputDocs/              documents, one subfolder per category, as in the ITU repo
        Inputs.md             manifest in the ITU Inputs.md format (generated)
        UAE_Policies_Regulations/  Swiss_Policies_Regulations/
        Global_Standards_Guidance/ AI_Use_Cases/
      chromadb/               ChromaDB database built with the ITU reference code

Steps:

1. Copy. Every registered file the drills search (data/sources.csv, not marked
   retrieval_excluded) is copied from data/raw/ into its InputDocs/ category, and each
   copy's SHA-256 hash is checked against the register. data/raw/ is not changed.
2. Ingest (--ingest). The ITU ingestion functions (https://github.com/CrashingGuru/ITUAIReadiness,
   cloned into vendor/ITUAIReadiness) are called unmodified, the same way the ITU command
   `python -m server.knowledge.ingest --dir InputDocs` calls them: framework definitions
   into kb_framework, every category into kb_main, and AI_Use_Cases also into kb_usecase.
   The only addition is metadata from the register (ID, title, jurisdiction, legal status,
   language, source URL) and the correct `country`, which the ITU filename patterns do not
   detect for the UAE or Switzerland.
3. Manifest. InputDocs/Inputs.md is regenerated, with chunk counts when a database exists.

    python scripts/build_knowledge_base.py            # copy + manifest
    python scripts/build_knowledge_base.py --ingest   # copy + build the database + manifest
    python scripts/build_knowledge_base.py --check    # only check the copies against the register
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
ITU_REPO = ROOT / "vendor" / "ITUAIReadiness"
ITU_SIM = ITU_REPO / "simulation"
REGISTER = ROOT / "data" / "sources.csv"
KB_DIR = ROOT / "knowledge-base"
INPUT_DOCS = KB_DIR / "InputDocs"
MANIFEST = INPUT_DOCS / "Inputs.md"
INDEX_DIR = KB_DIR / "chromadb"

# InputDocs/ category (ITU document_category) -> description. Order is the manifest order.
CATEGORIES = {
    "UAE_Policies_Regulations": "United Arab Emirates (UAE): federal and Dubai laws, regulations, policies and AI strategy",
    "Swiss_Policies_Regulations": "Switzerland (CH): federal acts, ordinances and official guidance",
    "Global_Standards_Guidance": "Global: ITU reports, international guidance and reference regulations",
    "AI_Use_Cases": "ITU standards for the AI use case (as in the ITU repo, also loaded into the `kb_usecase` collection)",
}
FOLDER_CATEGORY = {"ae": "UAE_Policies_Regulations", "ch": "Swiss_Policies_Regulations", "global": "Global_Standards_Guidance"}
USE_CASE_DOCS = {"ITU-STANDARDS-Y3172"}  # ITU files Y.3172 under AI_Use_Cases/
COUNTRY = {"AE": "United Arab Emirates", "CH": "Switzerland", "GLOBAL": "global"}

# Register legal status -> ITU source_type vocabulary (see ITU InputDocs/Inputs.md).
ITU_TYPE = {
    "national_strategy": "national_strategy",
    "international_standard": "standards_document",
    "standard": "standards_document",
    "framework_report": "international_org_report",
    "international_report": "international_org_report",
    "web_page_print": "international_org_report",
}  # everything else (laws, regulations, policies, guidance) -> policy_document

# Short, judge-readable reasons for files kept out (full notes are in data/sources.csv).
EXCLUSION_REASON = {
    "AE-DATA-PDPL-2021": "Unofficial translation; the official English text (AE-DATA-PDPL-2021-EN) is used instead",
    "AE-FEDERAL-DECREE-LAW-38-2024-AR": "Arabic text layer garbled on extraction; the English text is used for search",
    "AE-FEDERAL-DECREE-LAW-38-2024-AR-OFFICIAL": "Official Arabic PDF, but its text layer is defective; kept to check wording",
    "AE-DHA-HEALTH-DATA-PROTECTION-PP11-2022-AR": "Arabic version of PP-11; duplicates the English version",
    "EU-MDR-2017-745-OJ": "Original Official Journal text; duplicates the consolidated version",
    "EU-IVDR-2017-746": "In vitro diagnostics regulation; out of scope for a retinal-image screening tool",
    "AE-FEDERAL-DECREE-LAW-21-2025-VETERINARY-AR": "Veterinary products law; out of scope for this use case",
    "AE-EDE-NATIONAL-ESSENTIAL-MEDICINES-2025": "Essential medicines list; out of scope for a medical-device incident",
}


def is_excluded(row: dict) -> bool:
    return (row.get("retrieval_excluded") or "").strip().lower() in {"1", "true", "yes"}


def load_register() -> list[dict]:
    with REGISTER.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def category(row: dict) -> str:
    if row["doc_id"] in USE_CASE_DOCS:
        return "AI_Use_Cases"
    return FOLDER_CATEGORY[Path(row["file"]).parent.name]


def source(row: dict) -> tuple[Path, str]:
    """The file that is searched (the OCR text where the register names one) and its registered hash."""
    if row.get("extraction_file"):
        return ROOT / row["extraction_file"], row["extraction_sha256"]
    return ROOT / row["file"], row["sha256"]


def copy_path(row: dict) -> Path:
    return INPUT_DOCS / category(row) / source(row)[0].name


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_copies(rows: list[dict]) -> list[str]:
    """Problems with InputDocs/: missing, changed or unexpected files."""
    problems = []
    expected = {copy_path(r): source(r)[1] for r in rows}
    for path, digest in expected.items():
        if not path.exists():
            problems.append(f"missing: {path.relative_to(ROOT)}")
        elif sha256(path) != digest:
            problems.append(f"hash differs from data/sources.csv: {path.relative_to(ROOT)}")
    if INPUT_DOCS.exists():
        for path in INPUT_DOCS.rglob("*"):
            if path.is_file() and path != MANIFEST and path not in expected:
                problems.append(f"not in the register: {path.relative_to(ROOT)}")
    return problems


def sync_copies(rows: list[dict]) -> None:
    """Copy each searched file into its InputDocs/ category; remove anything else."""
    expected = {copy_path(r): r for r in rows}
    if INPUT_DOCS.exists():
        for path in list(INPUT_DOCS.rglob("*")):
            if path.is_file() and path != MANIFEST and path not in expected:
                path.unlink()
        for d in sorted((p for p in INPUT_DOCS.rglob("*") if p.is_dir()), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()
    for path, row in expected.items():
        src, digest = source(row)
        if sha256(src) != digest:
            sys.exit(f"{row['doc_id']}: {src.relative_to(ROOT)} does not match its hash in data/sources.csv")
        if not path.exists() or sha256(path) != digest:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, path)
    problems = check_copies(rows)
    if problems:
        sys.exit("Copy check failed:\n  " + "\n  ".join(problems))
    print(f"InputDocs: {len(rows)} files copied and checked against data/sources.csv")


def itu_commit() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(ITU_REPO), "log", "-1", "--format=%h (%ad)", "--date=short"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def ingest(rows: list[dict]) -> None:
    """Build knowledge-base/chromadb/ with the unmodified ITU ingestion functions."""
    os.environ["AIREADY_CHROMADB_DIR"] = str(INDEX_DIR)
    sys.path.insert(0, str(ITU_SIM))
    from server.config import settings  # noqa: E402
    from server.knowledge.ingest import ingest_file, ingest_framework_definitions  # noqa: E402
    from server.knowledge.kb import KnowledgeBase  # noqa: E402

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    kb = KnowledgeBase(persist_dir=str(INDEX_DIR))
    kb.reset()
    ingest_framework_definitions(kb)
    for row in rows:
        cat = category(row)
        extra = {
            "document_category": cat,
            "doc_id": row["doc_id"],
            "title": row["title"],
            "country": COUNTRY.get(row["jurisdiction"], "global"),
            "jurisdiction": row["jurisdiction"],
            "legal_status": row["binding"],
            "language": row["language"],
            "source_url": row["source_url"],
        }
        n = ingest_file(copy_path(row), kb, extra_metadata=extra)
        if cat == "AI_Use_Cases":  # the ITU command loads AI_Use_Cases into kb_usecase as well
            ingest_file(copy_path(row), kb, collection_name=settings.kb_usecase_collection, extra_metadata=extra)
        print(f"  {row['doc_id']:48s} {n:5d} chunks", flush=True)
    print(f"KB stats: {kb.stats()}")


def read_index() -> dict | None:
    """Chunk counts per document and per collection from knowledge-base/chromadb/, if it exists."""
    if not (INDEX_DIR / "chroma.sqlite3").exists():
        return None
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(path=str(INDEX_DIR), settings=Settings(anonymized_telemetry=False))
    per_doc: dict[str, int] = {}
    for meta in client.get_collection("kb_main").get(include=["metadatas"])["metadatas"]:
        per_doc[meta["doc_id"]] = per_doc.get(meta["doc_id"], 0) + 1
    collections = {c.name: c.count() for c in client.list_collections()}
    return {"per_doc": per_doc, "collections": collections}


def md_cell(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def write_manifest(rows: list[dict], excluded: list[dict], missing: list[dict], index: dict | None) -> None:
    lines = [
        "# Input Documents Manifest",
        "",
        "Every document in the Borderline knowledge base (KB), in the format of the `InputDocs/Inputs.md`",
        "manifest of the International Telecommunication Union (ITU) AI Readiness reference code",
        "([CrashingGuru/ITUAIReadiness](https://github.com/CrashingGuru/ITUAIReadiness)). Each subfolder",
        "here is one document category, and every filename below links to the document.",
        "",
        "- **Overview of the knowledge base:** [`knowledge-base/README.md`](../README.md)",
        "- **The vector database:** [`knowledge-base/chromadb/`](../chromadb/)",
        "- **Source URL, issuer, retrieval date and SHA-256 hash of every file:**"
        " [`data/sources.csv`](../../data/sources.csv)",
        "",
        "Each file here is a copy of the registered file in `data/raw/`, checked against its hash.",
        "This manifest is generated by [`scripts/build_knowledge_base.py`](../../scripts/build_knowledge_base.py).",
        "",
    ]
    if index is not None:
        cols = index["collections"]
        lines += [
            f"**Last build:** {len(rows)} documents; {cols.get('kb_main', 0):,} chunks in `kb_main`, "
            f"{cols.get('kb_framework', 0)} ITU AI Readiness framework definitions in `kb_framework`, "
            f"{cols.get('kb_usecase', 0)} chunks in `kb_usecase`; ITU reference code at commit {itu_commit()}.",
            "",
        ]
    lines += ["---", ""]

    for cat, heading in CATEGORIES.items():
        group = [r for r in rows if category(r) == cat]
        lines += [f"## {cat}/ ({len(group)} files)", "", heading, ""]
        header = "| # | Filename | Type | Legal status | Language | Description |"
        rule = "|---|----------|------|--------------|----------|-------------|"
        if index is not None:
            header += " Chunks |"
            rule += "-------:|"
        lines += [header, rule]
        for i, r in enumerate(group, 1):
            name = copy_path(r).name
            desc = f"**{md_cell(r['title'])}.** {md_cell(r['issuer'])}, {md_cell(r['in_force_from'])}. ID `{r['doc_id']}`."
            if r.get("extraction_file"):
                desc += (" Optical character recognition (OCR) text of the registered original,"
                         f" [`{Path(r['file']).name}`](../../{quote(r['file'])}).")
            cells = [str(i), f"[`{md_cell(name)}`]({cat}/{quote(name)})",
                     f"`{ITU_TYPE.get(r['binding'], 'policy_document')}`", md_cell(r["binding"]), r["language"], desc]
            if index is not None:
                cells.append(str(index["per_doc"].get(r["doc_id"], 0)))
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")

    lines += [
        "---",
        "",
        f"## Registered but not in the knowledge base ({len(excluded)} files)",
        "",
        "These files stay in `data/raw/` for checking wording or provenance and are left out of search,",
        "as in the drills.",
        "",
        "| Filename | ID | Reason |",
        "|----------|----|--------|",
    ]
    for r in excluded:
        reason = EXCLUSION_REASON.get(r["doc_id"], "Excluded from retrieval; see the register notes")
        lines.append(f"| [`{md_cell(Path(r['file']).name)}`](../../{quote(r['file'])}) | `{r['doc_id']}` | {reason} |")
    lines += ["", f"## Registered but not obtained ({len(missing)})", ""]
    for r in missing:
        lines.append(f"- `{r['doc_id']}`: {md_cell(r['title'])}. No file; its content is treated as unknown.")
    lines += [
        "",
        "## Notes",
        "",
        "- Each chunk carries the ITU metadata (`source_file`, `source_type`, `country`, `chunk_index`,",
        "  `document_category`) plus `doc_id`, `title`, `jurisdiction`, `legal_status`, `language` and",
        "  `source_url` from the register. `country` comes from the register, because the ITU filename",
        "  patterns do not detect the UAE or Switzerland.",
        "- The drills cite passages from Borderline's own page-level index (`make ingest`), built from the",
        "  same files in `data/raw/`. That index keeps page numbers and stable passage IDs so every quote",
        "  can be checked word for word.",
        "- Prepared for the ITU AI for Good Sandbox Hackathon: United Arab Emirates, with acknowledgement to the UAE.",
        "",
    ]
    MANIFEST.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--ingest", action="store_true", help="also build knowledge-base/chromadb/ with the ITU code")
    mode.add_argument("--check", action="store_true", help="only check knowledge-base/InputDocs/ against the register")
    args = parser.parse_args()

    register = load_register()
    included = [r for r in register if r["file"] and not is_excluded(r)]
    excluded = [r for r in register if r["file"] and is_excluded(r)]
    missing = [r for r in register if not r["file"]]
    for r in included:
        if r["doc_id"] not in USE_CASE_DOCS and Path(r["file"]).parent.name not in FOLDER_CATEGORY:
            sys.exit(f"{r['doc_id']}: file is outside data/raw/{{ae,ch,global}}: {r['file']}")

    if args.check:
        problems = check_copies(included)
        for p in problems:
            print(f"❌ {p}")
        if problems:
            sys.exit(1)
        print(f"✅ knowledge-base/InputDocs/: all {len(included)} files match data/sources.csv")
        return

    sync_copies(included)
    if args.ingest:
        ingest(included)
    write_manifest(included, excluded, missing, read_index())


if __name__ == "__main__":
    main()
