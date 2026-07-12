#!/usr/bin/env bash
# Git-based Overleaf integration (Overleaf's official programmatic path: git access).
#
# Requirements: Overleaf account with git integration (premium feature, or self-hosted
# CE/Server Pro). Get a git token at Overleaf > Account Settings > Git Integration, then:
#   export OVERLEAF_GIT_TOKEN=olp_xxx          # required for clone over https
#   export OVERLEAF_HOST=git.overleaf.com      # optional (default)
#
# Usage:
#   .codex/scripts/overleaf_sync.sh clone <project-id-or-url> [dir]   # default: docs/paper-codex
#   .codex/scripts/overleaf_sync.sh pull   [dir]
#   .codex/scripts/overleaf_sync.sh push   [dir] ["commit message"]
#   .codex/scripts/overleaf_sync.sh status [dir]
#
# Workflow: writer edits LaTeX in the cloned dir; pull before every editing session; push after.
# Overleaf compiles server-side — no local LaTeX toolchain needed.
set -u -o pipefail

CMD="${1:?usage: overleaf_sync.sh clone|pull|push|status ...}"
HOST="${OVERLEAF_HOST:-git.overleaf.com}"

die() { echo "overleaf_sync: $*" >&2; exit 1; }

mask() { sed -E 's#(https://)[^@]*@#\1***@#g'; }

guard_push() { # refuse to push data/secrets to Overleaf
  local staged
  staged=$(git diff --cached --name-only)
  echo "$staged" | grep -E '(^|/)(data/|experiments/)|\.env$|\.pem$|_key|token' \
    && die "push blocked: staged paths look like data/secrets (see list above). Unstage them."
  while IFS= read -r f; do
    [ -f "$f" ] && [ "$(stat -c%s "$f")" -gt 52428800 ] \
      && die "push blocked: $f exceeds 50MB (Overleaf limit)."
  done <<< "$staged"
  return 0
}

case "$CMD" in
  clone)
    SRC="${2:?project id or URL required}"
    DIR="${3:-docs/paper-codex}"
    [ -e "$DIR/.git" ] && die "$DIR already contains a git repo"
    if [[ "$SRC" == *"://"* || -d "$SRC" ]]; then
      URL="$SRC"   # full URL or local path (used by the mechanics test)
    else
      [ -n "${OVERLEAF_GIT_TOKEN:-}" ] || die "OVERLEAF_GIT_TOKEN not set (Overleaf > Account Settings > Git Integration)"
      URL="https://git:${OVERLEAF_GIT_TOKEN}@${HOST}/${SRC}"
    fi
    git clone "$URL" "$DIR" 2>&1 | mask || die "clone failed"
    echo "cloned into $DIR"
    ;;
  pull)
    DIR="${2:-docs/paper-codex}"
    BR=$(git -C "$DIR" symbolic-ref --short HEAD) || die "cannot determine branch"
    git -C "$DIR" pull --no-rebase origin "$BR" 2>&1 | mask || die "pull failed"
    ;;
  push)
    DIR="${2:-docs/paper-codex}"
    MSG="${3:-writer: update $(date +%F)}"
    cd "$DIR" || die "no such dir: $DIR"
    BR=$(git symbolic-ref --short HEAD) || die "cannot determine branch"
    git add -A
    git diff --cached --quiet && { echo "nothing to push"; exit 0; }
    guard_push
    git -c user.email="${GIT_AUTHOR_EMAIL:-writer@lab}" -c user.name="${GIT_AUTHOR_NAME:-writer}" \
      commit -m "$MSG" >/dev/null || die "commit failed"
    # integrate concurrent Overleaf edits first (skip when remote branch doesn't exist yet)
    if git ls-remote --exit-code origin "$BR" >/dev/null 2>&1; then
      git pull --no-rebase origin "$BR" 2>&1 | mask || die "pull failed — resolve conflicts, then push again"
    fi
    git push -u origin "$BR" 2>&1 | mask || die "push failed (check token / concurrent edits)"
    echo "pushed: $MSG"
    ;;
  status)
    DIR="${2:-docs/paper-codex}"
    git -C "$DIR" remote -v | mask
    git -C "$DIR" status -sb
    ;;
  *) die "unknown command: $CMD" ;;
esac
