#!/usr/bin/env bash
# Link or copy literature-review-skills into a tool's skills directory.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Link or copy each skills/<name> directory that contains SKILL.md.

Options:
  --target <cursor|claude|codex|all>  Tool skill directory (default: all)
  --mode <copy|link>                  Copy files or create symlinks (default: link)
  --dry-run                           Print the plan and write nothing
  --target agents                     [[TODO-TEXT]]
  --project DIR                       [[TODO-TEXT]]
  --uninstall                         [[TODO-TEXT]]
  -h, --help                          Show this help

Copy mode also copies shared/ to <name>/shared in each destination skill.
Link mode reaches shared/ through the symlink target, requiring the repository root to remain available.

Destinations are under $HOME:
  cursor  ~/.cursor/skills/<name>
  claude  ~/.claude/skills/<name>
  codex   [[TODO-TEXT]]

Running the same link install again leaves correct symlinks unchanged.
A copy install replaces the contents of each destination skill directory.
EOF
}

TARGET="all"
MODE="link"
DRY_RUN=0
UNINSTALL=0
PROJECT=""
MARKER=".lrs-installed"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --target)
      if [[ $# -lt 2 ]]; then
        echo "error: --target needs a value" >&2
        exit 2
      fi
      TARGET="$2"
      shift 2
      ;;
    --target=*)
      TARGET="${1#*=}"
      shift
      ;;
    --mode)
      if [[ $# -lt 2 ]]; then
        echo "error: --mode needs a value" >&2
        exit 2
      fi
      MODE="$2"
      shift 2
      ;;
    --mode=*)
      MODE="${1#*=}"
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --uninstall)
      UNINSTALL=1
      shift
      ;;
    --project)
      if [[ $# -lt 2 ]]; then
        echo "error: --project needs a value" >&2
        exit 2
      fi
      PROJECT="$2"
      shift 2
      ;;
    --project=*)
      PROJECT="${1#*=}"
      shift
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$TARGET" in
  cursor|claude|codex|agents|all) ;;
  *)
    echo "error: --target must be cursor, claude, codex, agents, or all" >&2
    exit 2
    ;;
esac

case "$MODE" in
  copy|link) ;;
  *)
    echo "error: --mode must be copy or link" >&2
    exit 2
    ;;
esac

if [[ -n "$PROJECT" ]]; then
  if [[ ! -d "$PROJECT" ]]; then
    echo "error: --project directory not found: $PROJECT" >&2
    exit 1
  fi
  PROJECT="$(cd "$PROJECT" && pwd)"
  BASE="$PROJECT"
else
  BASE="$HOME"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="${SCRIPT_DIR}/skills"
SHARED_SRC="${SCRIPT_DIR}/shared"

if [[ ! -d "$SKILLS_SRC" ]]; then
  echo "error: skills directory not found: $SKILLS_SRC" >&2
  exit 1
fi

if [[ ! -d "$SHARED_SRC" ]]; then
  echo "error: shared directory not found: $SHARED_SRC" >&2
  exit 1
fi

dest_root_for() {
  case "$1" in
    cursor) printf '%s\n' "${BASE}/.cursor/skills" ;;
    claude) printf '%s\n' "${BASE}/.claude/skills" ;;
    codex|agents) printf '%s\n' "${BASE}/.agents/skills" ;;
  esac
}

tools=()
if [[ "$TARGET" == "all" ]]; then
  tools=(cursor claude agents)
else
  tools=("$TARGET")
fi

skills=()
shopt -s nullglob
for src in "$SKILLS_SRC"/*; do
  if [[ -d "$src" && -f "$src/SKILL.md" ]]; then
    skills+=("$src")
  fi
done
shopt -u nullglob

if [[ ${#skills[@]} -eq 0 ]]; then
  echo "error: no skills with SKILL.md under $SKILLS_SRC" >&2
  exit 1
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  dry_label="yes"
else
  dry_label="no"
fi

echo "literature-review-skills install"
echo "source: ${SKILLS_SRC}"
echo "shared: ${SHARED_SRC}"
echo "target: ${TARGET}"
echo "mode: ${MODE}"
echo "dry-run: ${dry_label}"
echo "home: ${HOME}"
if [[ -n "$PROJECT" ]]; then
  echo "project: ${PROJECT}"
fi
if [[ "$UNINSTALL" -eq 1 ]]; then
  echo "action: uninstall"
fi
echo

if [[ "$UNINSTALL" -eq 1 ]]; then
  actions=0
  for tool in "${tools[@]}"; do
    root="$(dest_root_for "$tool")"
    for src in "${skills[@]}"; do
      name="$(basename "$src")"
      dest="${root}/${name}"
      if [[ -L "$dest" ]]; then
        link_target="$(readlink "$dest")"
        if [[ "$link_target" != "$src" ]]; then
          if [[ -e "$dest" || "$link_target" != */skills/"$name" ]]; then
            echo "skip  ${dest}  (symlink not created by this repo)"
            continue
          fi
        fi
        actions=$((actions + 1))
        if [[ "$DRY_RUN" -eq 1 ]]; then
          echo "would remove link  ${dest}"
        else
          rm "$dest"
          echo "removed link  ${dest}"
        fi
      elif [[ -d "$dest" ]]; then
        if [[ ! -f "$dest/$MARKER" ]]; then
          echo "skip  ${dest}  (no ${MARKER} marker)"
          continue
        fi
        actions=$((actions + 1))
        if [[ "$DRY_RUN" -eq 1 ]]; then
          echo "would remove copy  ${dest}"
        else
          rm -rf "$dest"
          echo "removed copy  ${dest}"
        fi
      elif [[ -e "$dest" ]]; then
        echo "skip  ${dest}  (not a directory or symlink)"
      else
        echo "absent  ${dest}"
      fi
    done
  done
  echo
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "dry-run finished: ${actions} removal(s) planned, nothing written"
  else
    echo "finished: ${actions} removal(s)"
  fi
  exit 0
fi


actions=0
for tool in "${tools[@]}"; do
  root="$(dest_root_for "$tool")"
  for src in "${skills[@]}"; do
    name="$(basename "$src")"
    dest="${root}/${name}"
    actions=$((actions + 1))

    if [[ "$MODE" == "link" ]]; then
      if [[ -L "$dest" ]]; then
        current="$(readlink "$dest")"
        if [[ "$current" == "$src" ]]; then
          echo "unchanged  link  ${dest}"
          continue
        fi
        if [[ "$DRY_RUN" -eq 1 ]]; then
          echo "would replace link  ${dest}  (now -> ${current})"
        else
          ln -sfn "$src" "$dest"
          echo "replaced link  ${src}  ->  ${dest}"
        fi
      elif [[ -e "$dest" ]]; then
        echo "error: ${dest} exists and is not a symlink; refusing to replace it" >&2
        exit 1
      else
        if [[ "$DRY_RUN" -eq 1 ]]; then
          echo "would link  ${src}  ->  ${dest}"
        else
          mkdir -p "$root"
          ln -sfn "$src" "$dest"
          echo "linked  ${src}  ->  ${dest}"
        fi
      fi
    else
      if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "would copy  ${src}  ->  ${dest}"
      else
        if [[ -e "$dest" && ! -d "$dest" && ! -L "$dest" ]]; then
          echo "error: ${dest} exists and is not a directory" >&2
          exit 1
        fi
        mkdir -p "$root"
        if [[ -L "$dest" ]]; then
          rm "$dest"
        fi
        mkdir -p "$dest"
        find "$dest" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
        cp -R "$src"/. "$dest"/
        echo "copied  ${src}  ->  ${dest}"
        # Copies have no repo root above them, so give each skill its own shared/.
        mkdir -p "$dest/shared"
        cp -R "$SHARED_SRC"/. "$dest/shared"/
        echo "copied  ${SHARED_SRC}  ->  ${dest}/shared"
        printf '%s\n' "$src" > "$dest/$MARKER"
      fi
    fi
  done
done

echo
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "dry-run finished: ${actions} action(s) planned, nothing written"
else
  echo "finished: ${actions} action(s) processed"
fi
