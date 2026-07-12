# Zotero integration guide

Connects the lab to your Zotero library via the Zotero Web API v3 (headless — no desktop app
needed on this machine). One tool, two surfaces: a CLI agents call via Bash, and the `zotero` MCP
server registered in `.codex/config.toml`, which loads when a Codex session starts.

## One-time setup (per user)

1. Get your credentials at https://www.zotero.org/settings/keys :
   - **userID** — the number shown at the top of that page ("Your userID for use in API calls").
   - **API key** — "Create new private key"; check *Allow library access* (read), and *Allow
     write access* if you want agents to save discovered papers into your library (recommended —
     the save-back workflow needs it).
2. Fill `.codex/settings.local.json` (gitignored):
   `"ZOTERO_API_KEY": "…", "ZOTERO_USER_ID": "…"` — or `ZOTERO_GROUP_ID` for a shared group
   library instead.
3. On a fresh checkout, launch Codex once and review/trust the project. Start a new session, then run
   `codex mcp list` and confirm `zotero` is `enabled`.
4. Verify credentials with `python3 .codex/scripts/zotero_mcp.py collections` — it should list
   your collections.

Alternative: if Zotero desktop runs on the same machine, `ZOTERO_LOCAL=1` uses its local API
(http://localhost:23119) with no key at all.

## What the agents do with it

| Agent | Usage |
|:--|:--|
| `brainstorm` | **Library-first**: searches your Zotero before the open web; reads Zotero-stored PDFs (`fulltext`); **save-back**: papers that become load-bearing are added to your library tagged with the HYP id |
| `critic` | Verifies that cited works actually exist (Zotero + lit_search cross-check) |
| `writer` | Exports BibTeX from Zotero into the Overleaf paper's `.bib` — never hand-writes entries Zotero can generate |

## Commands

```bash
python3 .codex/scripts/zotero_mcp.py search "eeg emotion" --limit 10 [--tag HYP-001]
python3 .codex/scripts/zotero_mcp.py item ABCD1234        # metadata + attachment/note keys
python3 .codex/scripts/zotero_mcp.py fulltext EFGH5678    # indexed text of a PDF attachment
python3 .codex/scripts/zotero_mcp.py bibtex ABCD1234,WXYZ9876   # BibTeX for the paper's .bib
python3 .codex/scripts/zotero_mcp.py collections
python3 .codex/scripts/zotero_mcp.py add --title "…" --doi 10.x/y --venue "…" --date 2025 --tag HYP-002
```

MCP tool names (same functions, loaded next session): `zotero_search`, `zotero_item`,
`zotero_fulltext`, `zotero_bibtex`, `zotero_collections`, `zotero_add`.

After changing `.codex/config.toml` or `.codex/settings.local.json`, start a new
`./orchestrate codex` session. Existing sessions do not acquire newly configured MCP tools.

## Troubleshooting

| Symptom | Meaning | Fix |
|:--|:--|:--|
| MCP tools absent | project is not trusted or current session predates the configuration | review/trust the project, confirm `codex mcp list`, then restart through `./orchestrate codex` |
| "Zotero not configured" | env vars missing | fill `.codex/settings.local.json`, restart session (env loads at start) |
| HTTP 403 | key invalid or lacks access | regenerate at zotero.org/settings/keys; check library access boxes |
| `add` fails with 403 | key is read-only | recreate the key with write access |
| `fulltext` 404 | key is a parent item, not the PDF | run `item <parent>` and use the attachment child key |
| Empty search results | term not in library | that's the honest answer — fall back to `lit_search` (open web) |
