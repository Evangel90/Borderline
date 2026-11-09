# Borderline Knowledge Base

**Policies, regulations and strategies for cross-border incidents in medical AI:
United Arab Emirates (UAE), Switzerland and global guidance.**

This folder is the complete knowledge base (KB) of [Borderline](../README.md), built for the
International Telecommunication Union (ITU) AI for Good Sandbox Hackathon: United Arab Emirates.
It follows the layout of the ITU AI Readiness reference code
([CrashingGuru/ITUAIReadiness](https://github.com/CrashingGuru/ITUAIReadiness)) and was built
with that code: each document is parsed, split into passages, embedded with the
`nomic-embed-text` model and stored in a ChromaDB vector database.

**Start here:**

- **[Document list (Inputs.md)](InputDocs/Inputs.md):** every document, with a link to the file, its type, legal status, language and passage count
- **[The documents (InputDocs/)](InputDocs/):** 40 files in four category folders
- **[The vector database (chromadb/)](chromadb/):** ready to search; see [Search it](#search-it)
- **[Source register (sources.csv)](../data/sources.csv):** source URL, issuer, retrieval date and SHA-256 hash of every file

## Layout

```
knowledge-base/
  README.md                          this page
  InputDocs/                         the documents, as in the ITU repo
    Inputs.md                        the manifest
    UAE_Policies_Regulations/        19 files
    Swiss_Policies_Regulations/       9 files
    Global_Standards_Guidance/       11 files
    AI_Use_Cases/                     1 file: ITU-T Y.3172
  chromadb/                          the vector database
```

| | |
|---|---|
| Documents | **40**: 19 UAE, 9 Swiss, 11 global, plus ITU-T Y.3172 under AI use cases |
| Passages | **2,247** in `kb_main`, plus **19** ITU AI Readiness framework definitions (13 dimensions and 6 factors) |
| Built with | ITU reference code at commit `84010da`, `nomic-embed-text` embeddings, ChromaDB 1.5.9 |

## Why the documents are also in `data/raw/`

The files in `InputDocs/` are byte-identical copies of files in [`data/raw/`](../data/raw/).
This is deliberate:

- **`data/raw/` is the project's source archive.** It holds all 48 registered files, including
  8 kept out of search but retained to check wording or provenance. The drills, their passage
  files and the four published runs cite these paths, so the files stay where they are.
- **`InputDocs/` is the knowledge base as a self-contained folder.** It holds only the 40
  documents that are searched, in the ITU layout, so it can be passed to the ITU ingestion
  command or moved into the ITU AI for Good Lab without the rest of the repository.
- **The copies cannot drift.** `make knowledge-base` copies each file from `data/raw/` and checks
  it against its SHA-256 hash in [`data/sources.csv`](../data/sources.csv);
  `make verify-knowledge-base` re-checks all 40 at any time.
- **No extra storage.** Git stores identical files once, so the copies add almost nothing to the
  repository's size.

## What is in it

**UAE (19).** Federal laws on personal data protection (Federal Decree-Law 45/2021), information
and communications technology (ICT) in health (Federal Law 2/2019 and its executive regulation),
medical products (Federal Decree-Law 38/2024), the Emirates Drug Establishment and its
pharmacovigilance guideline, cybercrime and the Emirates Data Office; Dubai Law 26/2015 on data
exchange; Dubai Health Authority (DHA) policies on AI in healthcare, health-data protection
(PP-11), information sharing (PP-13), patient referral and sentinel events; the National
Strategy for AI 2031, the UAE AI Charter, the AI ethics guidelines and the AI adoption
guidelines for government services.

**Switzerland (9).** The Federal Act on Data Protection (FADP) and its ordinance, the Therapeutic
Products Act and the Medical Devices Ordinance, the Human Research Act, the cyberattack reporting
duty and its ordinance, and official factsheets.

**Global (11).** The ITU AI Readiness framework report, World Health Organization (WHO) guidance
on AI for health, the United Nations *Governing AI for Humanity* report, the G7 Hiroshima code of
conduct, the European Union (EU) Medical Device Regulation (MDR) and its guidance on significant
changes, International Medical Device Regulators Forum (IMDRF) guidance, the US Food and Drug
Administration (FDA) guidance on predetermined change control plans, and the Organisation for
Economic Co-operation and Development (OECD) recommendation on privacy enforcement cooperation.

**AI use cases (1).** ITU-T Y.3172, the architectural framework for machine learning in future
networks, filed under `AI_Use_Cases/` as in the ITU repo. The use case itself (a fictional
diabetic-retinopathy screening product) is described in the
[synthetic product dossier](../report/synthetic-product-dossier-retinavision-dx.md); it is
fictional, so it is not part of the knowledge base.

## Inside the database

| Collection | Contents |
|---|---|
| `kb_main` | 2,247 passages from all 40 documents |
| `kb_framework` | 19 ITU AI Readiness framework definitions |
| `kb_usecase` | 50 passages from the `AI_Use_Cases/` documents (ITU-T Y.3172), as the ITU code does |
| `kb_decisions` | Empty; used by the ITU simulation game to record decisions |

Each passage carries the ITU metadata (`source_file`, `source_type`, `country`, `chunk_index`,
`total_chunks`, `document_category`, `ingested_at`) plus `doc_id`, `title`, `jurisdiction`,
`legal_status`, `language` and `source_url` from the source register. Embeddings use
`nomic-embed-text` through Ollama (a local model runner) with cosine distance.

## Search it

Needs `pip install chromadb ollama`, and `ollama pull nomic-embed-text` with `ollama serve` running.

```python
import chromadb, ollama

db = chromadb.PersistentClient(path="knowledge-base/chromadb")
kb = db.get_collection("kb_main")
question = "When may health data be transferred outside the UAE?"
vector = ollama.embed(model="nomic-embed-text", input=[question])["embeddings"][0]
hits = kb.query(query_embeddings=[vector], n_results=5,
                where={"country": "United Arab Emirates"})
for meta, text in zip(hits["metadatas"][0], hits["documents"][0]):
    print(meta["doc_id"], "|", text[:120])
```

To use it inside the ITU simulation, set `AIREADY_CHROMADB_DIR` to the full path of
`knowledge-base/chromadb`.

## Rebuild it

**With the ITU command, unchanged.** From a clone of the ITU repo, in its `simulation/` folder:

```bash
AIREADY_CHROMADB_DIR=/path/to/new-db AIREADY_INPUT_DOCS_DIR=/path/to/Borderline/knowledge-base/InputDocs \
  python -m server.knowledge.ingest --reset --dir /path/to/Borderline/knowledge-base/InputDocs
```

This reproduces the same documents and passages (checked on 9 November 2026: 2,247 passages from 40 files, 19 framework definitions and 50 use-case passages, the same counts as the committed database). Without our script the ITU code
does not add the register metadata, and it tags UAE and Swiss passages with country "global",
because its filename patterns do not detect those countries.

**With Borderline's build (adds the register metadata).** From the repository root, after step 1
of the [reproducibility guide](../README.md#1-install):

```bash
git clone https://github.com/CrashingGuru/ITUAIReadiness vendor/ITUAIReadiness
git -C vendor/ITUAIReadiness checkout 84010da
.venv/bin/pip install -e ".[itu]"
ollama pull nomic-embed-text       # with `ollama serve` running
make knowledge-base                # refreshes InputDocs/, chromadb/ and Inputs.md
make verify-knowledge-base         # checks every file in InputDocs/ against the register
```

[`scripts/build_knowledge_base.py`](../scripts/build_knowledge_base.py) copies each registered
file from `data/raw/` into `InputDocs/`, checks the copy's hash, and calls the ITU ingestion
functions unmodified. `data/raw/` holds all 48 registered files; 8 of them stay out of the
knowledge base, as they do in the drills: duplicates, texts outside the medical-device scope,
Arabic files whose text layer is defective, and one unofficial translation. Each is listed in
[Inputs.md](InputDocs/Inputs.md) with its reason.

The drills themselves search a separate page-level index built from `data/raw/` (`make ingest`),
which keeps page numbers so every quoted passage can be checked word for word.

Prepared with acknowledgement to the UAE.
