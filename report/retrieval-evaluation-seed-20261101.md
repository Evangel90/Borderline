# Retrieval seed evaluation

**Date:** 1 November 2026. **Data:** `data/retrieval_benchmark_seed.csv`, ten manually selected questions with exact passage IDs and jurisdiction filters.

| Search mode | Exact passage in top 3 | Exact passage in top 6 |
|---|---:|---:|
| Vector only, before change | 6/10 | 6/10 |
| Hybrid vector and lexical | 8/10 | 9/10 |

The remaining miss is `R-010`: the WHO passage on re-identification was outside the top six. The seed deliberately includes known documents and several exact-term questions. It does not measure general retrieval quality, citation support, mandate applicability, or legal accuracy. The new scoring still requires a larger reviewed set and run-level inspection for off-topic evidence.

Reproduce with `make evaluate-retrieval`. `KnowledgeIndex.search` now merges vector and lexical candidates, weights rare matching terms, and enforces jurisdiction and document filters on both candidate paths. A focused filter test is included in the test suite.
