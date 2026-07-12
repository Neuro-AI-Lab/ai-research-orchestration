---
name: research-paper-workflow
description: Run an evidence-grounded AI research paper pipeline from outline and Zotero bibliography through Overleaf drafting, scientific review, artifact verification, revision, and submission readiness. Use for paper planning, writing, review, and reference management.
---

# Research paper workflow

Before drafting, freeze a claim-evidence matrix linking each proposed contribution, number, table, and
figure to cleared Codex HYP/EXP/REPORT/REV IDs or verified primary sources. Remove or mark unsupported
claims. Build the bibliography from verified Codex Zotero item keys and deduplicate identifiers.

Use this cycle:

1. `writer` creates an outline with claim/evidence links and explicit limitation slots.
2. Pull the Overleaf repository with `.codex/scripts/overleaf_sync.sh` and inspect status before edits.
3. Draft methods from code/config and results from cleared records; retain provenance in comments or a
   local claim map without exposing secrets.
4. `critic` reviews scientific validity, novelty calibration, related-work coverage, and claim strength.
5. `qa` verifies citations, figure/table source data, cross-references, compilation, artifact links, and
   that every revision addresses the recorded review.
6. `writer` revises without silently deleting caveats. Repeat at most three cycles, then escalate a
   structural blocker.

Pull before each editing session. Never resolve a merge conflict by discarding remote work. Never push
to Overleaf, save references, or change external state without user authority. Before submission, record
the exact draft commit, bibliography snapshot, code/data availability, ethics/license constraints,
limitations, unresolved issues, and critic/QA clearance.
