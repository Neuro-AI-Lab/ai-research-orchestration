---
name: grounded-research-writing
description: Write research reports, paper sections, READMEs, captions, and summaries with traceable claims, exact sourced numbers, calibrated uncertainty, preserved caveats, and no invented evidence. Use whenever AI research findings are communicated.
---

# Grounded research writing

Map every number, citation, and empirical claim to a Codex EXP/REPORT/REV entry, retained log, or fetched
primary source. Preserve recorded values exactly; do not round, clean up, or fill gaps from memory. If
evidence is absent or ambiguous, state that rather than generating a plausible result.

Separate:

- **Observation:** what the artifact records.
- **Interpretation:** what the cleared evidence supports.
- **Limitation:** unresolved validity, data, or generalization constraints.
- **Speculation:** explicitly labeled future explanation or hypothesis.

Use strength calibrated to evidence: single-run deltas `suggest`; replicated effects with appropriate
uncertainty may `show`; avoid `prove`, `novel`, or `state of the art` without direct support. Preserve
negative and null results, failed runs, reviewer concerns, and dataset limitations.

Describe methods from the shipped code/config, not the intended design. Put long-form drafts in their
own files and index them from `.codex/research/discussion.md`. Drafts reporting experimental findings
require a passed critic result review. Use plain, precise prose without marketing language.
