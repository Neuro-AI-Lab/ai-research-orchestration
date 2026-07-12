---
name: literature-evidence-review
description: Build traceable AI research literature maps from primary sources using literature search and Zotero tools, with verified metadata, evidence-level labeling, contradiction tracking, and citation hygiene. Use for literature reviews, novelty checks, related work, and evidence grounding.
---

# Literature evidence review

Define the question, concepts, date range, venues, inclusion/exclusion criteria, and stopping condition
before searching. Search the Codex Zotero library first, then configured literature MCP sources, then
the open web only for gaps. Deduplicate by DOI, arXiv ID, PMID, title, and version.

Treat search snippets and abstracts as leads. Fetch and read the primary paper sections needed for a
claim. Label evidence as `full text`, `methods/results inspected`, `abstract only`, or `unverified`.
Prefer original papers, official datasets, and released code over secondary summaries.

For each included source, record a RES entry with:

- stable identifier and verified bibliographic metadata;
- research question, data, method, baselines, metrics, and sample/evaluation unit;
- exact claim relevant to this project and its evidence level;
- limitations, contamination/replication concerns, and source version;
- relation to HYP entries and agreements or contradictions with other sources.

Never invent an author, title, venue, DOI, number, or finding. Do not cite a paper for a claim it merely
cites elsewhere. Mark retractions, corrections, non-peer-reviewed status, and unavailable full text.
Save verified references through the Codex Zotero integration and use stable item keys in drafts.
