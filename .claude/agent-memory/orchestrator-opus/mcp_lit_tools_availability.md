---
name: mcp-lit-tools-availability
description: The literature/Zotero MCP tools promised in agent specs may be absent from a specialist's actual toolset; brainstorm/critic silently fall back to WebSearch.
metadata:
  type: feedback
---

Do not assume the `lit_search` / `zotero_search` MCP tools are available to brainstorm or critic just because the agent spec and `.mcp.json` describe them.

**Why:** On 2026-07-08 (PLAN-2026-28), brainstorm reported the MCP `lit_search`/`zotero_search` tools were not present in its toolset that session and fell back to WebSearch/WebFetch (which worked — 11 prior works verified with DOI/PMID — but the Zotero library-first rule and save-back could not be honored). brainstorm and critic also lack Bash, so they cannot run the `lit_search.py`/`zotero_mcp.py` shell scripts as a fallback either.

**How to apply:** When a novelty/citation-verification task depends on the literature tools, tell the specialist in the brief to use the MCP tools if present and WebSearch/WebFetch otherwise, and to state in its RESULT which path it used. If Zotero library-first / save-back is important for the task, route the Zotero write through a Bash-capable path or note it as an open item. See also [[pdf-input-preflight]].
