---
name: pdf-input-preflight
description: Before fanning out specialists onto a PDF/binary deliverable, verify the file is intact — the Read tool silently duplicates page 1 on corrupt multipage PDFs and reports success.
metadata:
  type: feedback
---

Before dispatching specialists to review a PDF (or any binary deliverable), run a cheap input-integrity pre-flight first. Do not assume "the file exists and page 1 renders" means the file is readable.

**Why:** On 2026-07-08 (PLAN-2026-28, review of example.pdf), three specialists were dispatched in parallel onto example.pdf. The file was structurally truncated — missing `%%EOF`/`xref`/`trailer`, only 7 of 13 declared `/Page` objects recoverable, pages 2–7 had empty `/Resources` (no fonts) so body text could not render. The Read tool, asked for pages "1-13", **silently returned page 1's image 13 times and reported success** — a dangerous silent-failure mode. Only the Bash-equipped data agent diagnosed the truncation (via `pdftotext`/`pdftoppm`/`pikepdf`/`qpdf`); Read-only agents (critic, brainstorm) saw blank pages 2–13. ~312k subagent tokens and ~10 min of tool time were spent largely diagnosing a broken file instead of reviewing it.

**How to apply:** For any PDF-review task, before fan-out either (a) have one Bash-capable agent (data or filemanager) confirm the file has a valid trailer/xref/`%%EOF` and that page count matches the declared count, or (b) instruct reviewers to cross-check the rendered page count against the expected count and to prefer per-page reads / `pdftotext -f N -l M` over a single wide range request. Treat a single-agent triage as cheap insurance before a multi-agent fan-out on a binary input. See also [[mcp-lit-tools-availability]].
