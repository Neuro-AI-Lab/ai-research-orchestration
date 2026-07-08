---
name: pdf-multipage-render-bug
description: A corrupt/truncated PDF can make the Read tool silently render only page 1 (blank or duplicated pages beyond that) with no error — verify with a spot-check before trusting a multi-page PDF review, but do not assume the Read tool itself is broken.
metadata:
  type: project
---

Observed 2026-07-08 reviewing `example.pdf` (13-page IEEE manuscript). First attempt, against a
17.6MB copy of the file: the `Read` tool's PDF page extraction was unreliable beyond page 1 —
`pages: "1-13"` returned 13 images all showing page 1's content (silent duplication, no error); any
single non-first page or range not starting at 1 returned blank images; confirmed deterministic
across repeated isolated retries.

**Resolution (2026-07-08, same day):** the file was re-exported (25MB, `%%EOF`/`startxref` present,
`pdfinfo` reported 13 pages with no syntax errors). Re-reading with `pages: "1-13"` rendered all 13
pages correctly with distinct content. This strongly suggests the original failure was **file
corruption/truncation in that specific PDF**, not a systemic Read-tool defect with multi-page PDFs in
this environment.

**Why:** A truncated or malformed PDF (missing/broken xref table, incomplete object streams) can
cause a PDF-to-image pipeline to fail silently on later pages while still succeeding on page 1 (often
cached/parsed first), rather than raising an error.

**How to apply:** Before trusting a multi-page PDF review, spot-check that at least one non-first
page renders distinct content. If it doesn't: (1) don't fabricate content for the unreadable pages —
write the review as explicitly partial/UNVERIFIED, per the discipline `_review_critic.md` followed on
first attempt; (2) suspect file corruption first (check for `%%EOF`/`startxref`, run `pdfinfo` if
Bash is available, ask for a re-export) rather than concluding the Read tool cannot handle multi-page
PDFs in general — this environment's Read tool successfully rendered all 13 pages once given an
intact file. Do not over-generalize a single corrupt-file failure into "multi-page PDFs don't work
here."
