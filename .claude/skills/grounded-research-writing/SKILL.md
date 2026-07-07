---
name: grounded-research-writing
description: >-
  Write human-facing research prose — experiment narratives, progress reports, paper
  sections, READMEs, figure captions — that stays strictly grounded in recorded
  results, with every number and claim traceable to a source and no overstated
  conclusions. Use this skill whenever the user asks to write up, summarize, or report
  AI/modeling results, draft a paper section, or "turn these results into" prose.
  Trigger it whenever results are being communicated to people — confident,
  fluent-sounding writing is exactly where fabricated numbers and overclaims slip in,
  so prefer this discipline over free-form summarization.
---

# Grounded research writing

Fluent research prose is the easiest place for an unsupported number or an inflated
claim to hide — it *sounds* authoritative regardless of whether it is true. The job
here is to synthesize recorded results into clear writing while guaranteeing that
every quantitative claim traces to a source and no conclusion outruns the evidence.
Synthesize; never invent.

## The grounding rule (the central discipline)

- **Every number, result, and citation must be traceable to a recorded source** — an
  experiment ID, a result entry, a logged metric. The sentence or its surrounding
  context names that source. No untraceable numbers, ever.
- **Preserve numbers exactly** as recorded when summarizing; paraphrase the prose
  around them, but do not "clean up", round, or adjust a value.
- **If a requested result does not exist, say so.** Do not generate a plausible
  number to fill the gap. A missing result is reported as missing.
- **If a source entry is ambiguous, ask** rather than smoothing it over with
  confident-sounding prose.

## Honest claims

- Use hedged language matched to the evidence: "the result is consistent with the
  hypothesis" rather than "we proved the hypothesis."
- Reserve "shows" / "demonstrates" for findings with established statistical support
  (variance across seeds, confidence intervals, or a significance test). A single-run
  delta gets "suggests" or "is consistent with", not "shows".
- Avoid "novel" unless a contribution has actually been identified against prior work.
- Do not silently drop caveats. If a validity review raised a concern about leakage,
  baseline fairness, or confounders, surface it in the write-up — including the
  dataset definition and its limitations — rather than presenting a clean story.
- Report a reviewer's stance; do not adopt one the evidence doesn't support. Writing
  about a result does not give license to declare a hypothesis confirmed.

## Structure

Keep summaries tight — a few sentences of plain-English summary, then the numbers in
a table with their sources, then an honest assessment.

```markdown
## [report-id] short title | YYYY-MM-DD
**Covers:** <experiment ids>   **Hypothesis:** <id>

### Summary
<2–4 sentences, plain English, no wall of text>

### Key numbers
| Metric | Value | Source     |
|:-------|:------|:-----------|
| ...    | ...   | <exp-id>   |   <- every row cites where it came from

### Assessment
- **Consistent with:** <hypothesis / review id>
- **Does not show:** <honest caveat, linked to the review that raised it>
- **Open questions:** <what remains untested>
```

Long-form deliverables (paper drafts, full reports) go in their own files, with a
short index entry pointing to them rather than pasting the whole thing inline.

## Method sections

When describing what a model or pipeline does, describe what the **code actually
does**, not what the hypothesis hoped it would do. Read the implementation if
needed — a method section that describes the intended design instead of the shipped
one is a subtle form of fabrication.

## Style

Sentence case for headings; no title case, no ALL CAPS. No emojis, no exclamation
marks, no marketing language ("groundbreaking", "state-of-the-art" without a
citation). Plain, precise, honest prose. Brevity over volume — a tight paragraph that
every number backs up beats a long one that drifts from the evidence.
