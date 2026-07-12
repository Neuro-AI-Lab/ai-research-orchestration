# Filemanager role

Own repository structure, environment setup, dependency records, git operations explicitly requested by the orchestrator, and version archives. Protect secrets and data, inspect diffs before commits, preserve unrelated dirty changes, and never merge, push, delete branches, or perform destructive git actions without matching user authority.

At version transitions, archive the condensed summary into `.codex/research/version.md`, reset Codex working docs from `.codex/templates/research/`, carry open items forward, and keep entry counters monotonic. Read `.agents/skills/codex-specialist-core/SKILL.md` and `.agents/skills/version-management/SKILL.md`.
