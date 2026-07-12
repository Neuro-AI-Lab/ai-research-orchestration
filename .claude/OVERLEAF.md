# Overleaf integration guide

Git-based Overleaf collaboration (Overleaf's official programmatic path — there is no public
editing API). Once a project is linked, the `writer` agent edits LaTeX locally with full grounding
discipline and syncs with Overleaf; you see changes live on the Overleaf web editor, which also
does the compiling.

## One-time setup (per user)

1. Get a git token: Overleaf → Account Settings → **Git Integration** → Generate token
   (`olp_...`). Git integration is an Overleaf premium feature (institutional licenses usually
   include it).
2. Copy `.claude/settings.local.json.example` to `.claude/settings.local.json` and paste your
   token into `OVERLEAF_GIT_TOKEN`. That file is gitignored (as are `docs/paper-claude*/` clones) —
   never commit a real token.
3. Optional sanity check that the token authenticates (any fake project id works; "no git
   access / project does not exist" means auth passed, "Authentication failed" means bad token):
   `git ls-remote https://git:$OVERLEAF_GIT_TOKEN@git.overleaf.com/000000000000000000000000`

The token authenticates account-wide; no further token steps are needed per project.

Security notes:
- Rotate the token any time at Overleaf → Account Settings → Git Integration; then update
  `.claude/settings.local.json` — nothing else references it (clones embed it in their remote URL,
  so re-clone or `git remote set-url` after a rotation).
- Never put the token in `settings.json`, agent specs, or Claude research docs (those are checked in).

## Linking a work project (repeat per paper/project)

1. Open the project on Overleaf; copy its ID from the URL:
   `https://www.overleaf.com/project/`**`<project-id>`**
2. Clone it (pick a name for multi-project setups; the default dir is `docs/paper-claude`):

   ```bash
   .claude/scripts/overleaf_sync.sh clone <project-id> docs/paper-claude-<short-name>
   ```

3. Verify: `.claude/scripts/overleaf_sync.sh status docs/paper-claude-<short-name>` — remote shows
   `https://***@git.overleaf.com/<project-id>` (token masked) and a clean tree.
4. Tell the orchestrator which HYP/EXP scope this paper covers; the `writer` agent takes it from
   there (pull-first → edit with `% source: EXP-NNN` provenance comments → push with doc-ID
   commit messages → critic gate before any section is reported "done").

## Day-to-day commands (writer runs these; you rarely need them)

| Action | Command |
|:--|:--|
| Get latest (incl. your web edits) | `.claude/scripts/overleaf_sync.sh pull docs/paper-claude-<name>` |
| Push agent edits | `.claude/scripts/overleaf_sync.sh push docs/paper-claude-<name> "writer: results (EXP-003)"` |
| Check state | `.claude/scripts/overleaf_sync.sh status docs/paper-claude-<name>` |

Push safety is built in: refuses staged `data/`/secret-looking paths and >50MB files, integrates
concurrent Overleaf edits before pushing, masks the token in all output.

## Troubleshooting

| Symptom | Meaning | Fix |
|:--|:--|:--|
| `no git access ... project does not exist, or git access is not enabled` | wrong project ID, or the project owner's plan lacks git integration | re-copy the ID; confirm premium/institutional plan on the project owner's account |
| `Authentication failed` | token revoked/rotated | new token → update `.claude/settings.local.json`; re-clone or `git remote set-url` |
| push rejected, "resolve conflicts" | simultaneous web + agent edits collided | writer resolves (user's web edits win unless factually wrong), pushes again |
| clone works but env var missing in-session | `settings.local.json` env loads at session start | one-off: prefix the command with `OVERLEAF_GIT_TOKEN=... ` |
