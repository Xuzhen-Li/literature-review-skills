# Gemini fact bundle — literature-review-skills PR #2 (`feat/install-targets`)

Read-only facts for writing. Do not invent behaviour. Write only the slots listed under Output.
This file is a fact sheet only. Do not write the prose into this file.

Repo local clone: `/workspace/litreview-pr2`
Branch HEAD: `d7ec2b5` (Test shared/ resolution and removal for every target, mode and scope)
Upstream: `Xuzhen-Li/literature-review-skills` branch `feat/install-targets`
Prose request list: `/workspace/litreview-pr2-prose-needed.md` (also mirrored conceptually below)

## Rules for the writer

- Facts only from this bundle.
- zh and en blocks each complete and aligned sentence-for-sentence where both languages are required.
- ASCII symbols only. Use ASCII hyphen `-` where a hyphen is needed (flags, changelog dates, paths). No em dash, en dash, or arrow characters inside the written prose.
- No filler. No citation markers.
- Never write the letters GBTS. Do not name models or writing tools.
- Code names and paths in backticks exactly as in code: `install.sh`, `skills/<name>`, `SKILL.md`, `shared/`, `--target`, `--mode`, `link`, `copy`, `--dry-run`, `--uninstall`, `--project`, `cursor`, `claude`, `codex`, `agents`, `all`, `.lrs-installed`, `~/.agents/skills`, `~/.claude/skills`, `~/.cursor/skills`, `~/.codex/skills`, `tests/test_install.py`.
- Do not change fenced code blocks in the READMEs unless a slot below explicitly replaces lines inside one. Prefer leaving the existing bash and pytest fences intact and putting new examples in surrounding prose or new lines the parent will splice later.
- Output format: one slot per block as `file:line -> new text` (use the ASCII sequence `->` only as the slot separator in the delivery file, not inside the prose sentences).
- Delivery file for the later writing pass: `/workspace/litreview-pr2-prose-text.md` (or `/workspace/litreview-pr2/prose-text.md` if the parent redirects). This bundle does not write that file.

## Required content flags (must appear in the written prose)

1. README en, README zh, and CHANGELOG each need **one sentence** saying old `~/.codex/skills` is **not** cleaned automatically and the user may delete it by hand.
2. README en and zh need an **uninstall scope** sentence: `--uninstall` removes only this repo's symlinks and copy directories that contain the `.lrs-installed` marker; unmarked copies from the PR #1 era are skipped (re-run a copy install first, or delete manually).
3. Help (`install.sh` `usage`) must be rewritten so it matches the code below (it is currently stale).

## Output slots

1. `install.sh` help (`usage` heredoc): full rewrite of the stale `-h` text so options, destinations, `all`, `--project`, `--uninstall`, and `.lrs-installed` match the Verified facts. English only.
2. `README.md` Install section: update lead / table / options / add uninstall and migration notes (en). Keep zh aligned.
3. `README.zh.md` Install section: same slots as en, Chinese, sentence-aligned.
4. `CHANGELOG.md`: new Unreleased (or next version) entry covering Changed and Added items listed in Verified facts. English. Include the one-sentence `~/.codex/skills` manual-cleanup note.

Suggested concrete replace points (current line numbers on HEAD `d7ec2b5`):

| Slot label | file:line | About |
|---|---|---|
| `README.md:72` | Install lead | still old one-liner; may keep shared/ behaviour if already true |
| `README.md:74-78` | Install table | still lists Codex as `~/.codex/skills`; needs user and project paths and agents |
| `README.md:88` | options paragraph | stale target list; no `--project` / `--uninstall` |
| `README.md` new | uninstall + migration | not present yet |
| `README.zh.md:72` | 安装 lead | align with en |
| `README.zh.md:74-78` | 安装 table | align with en |
| `README.zh.md:88` | options | align with en |
| `README.zh.md` new | uninstall + migration | not present yet |
| `CHANGELOG.md` | Unreleased / new section | no Unreleased today |
| `install.sh:-h` | full help | stale |

---

## Slot context — README.md Install (verbatim, lines 70-94)

````
    70|## Install
    71|
    72|`install.sh` links (default) or copies each `skills/<name>` directory that contains `SKILL.md`.
    73|
    74|| Tool | Destination |
    75||------|-------------|
    76|| Cursor | `~/.cursor/skills/<name>` |
    77|| Claude Code | `~/.claude/skills/<name>` |
    78|| Codex | `~/.codex/skills/<name>` |
    79|
    80|```bash
    81|bash install.sh --target cursor --mode link
    82|bash install.sh --target claude --mode copy
    83|bash install.sh --target codex
    84|bash install.sh --target all --dry-run
    85|bash install.sh -h
    86|```
    87|
    88|`--target` is `cursor`, `claude`, `codex`, or `all` (default `all`). `--mode` is `link` (default) or `copy`. `--dry-run` prints the plan and writes nothing. A second link install leaves correct symlinks unchanged. Start a new session so the tool reloads skills. Paths honor `$HOME`.
    89|
    90|Run the tests from this repository:
    91|
    92|```bash
    93|python3 -m pytest
    94|```
````

### What is needed (README en)

- Install table per platform (Claude Code, Codex, Cursor, other Agent Skills tools): target name, user path, project path.
- Codex destination is now `~/.agents/skills/<name>` (same path as `agents`).
- Add `agents` target row / path.
- Project-scope paths when `--project DIR` is set: `DIR/.claude/skills`, `DIR/.agents/skills`, `DIR/.cursor/skills`.
- One sentence: old installs under `~/.codex/skills` are not removed automatically; the user may delete them by hand. `--uninstall` does not touch `~/.codex/skills`.
- Uninstall section / sentences covering scope (see Verified facts).
- Note that copy installs from the PR #1 era have no `.lrs-installed` marker and are skipped by `--uninstall`.

---

## Slot context — README.zh.md 安装 (verbatim, lines 70-94)

````
    70|## 安装
    71|
    72|`install.sh` 脚本会链接（默认）或复制包含 `SKILL.md` 文件的每个 `skills/<name>` 目录。
    73|
    74|| Tool | Destination |
    75||------|-------------|
    76|| Cursor | `~/.cursor/skills/<name>` |
    77|| Claude Code | `~/.claude/skills/<name>` |
    78|| Codex | `~/.codex/skills/<name>` |
    79|
    80|```bash
    81|bash install.sh --target cursor --mode link
    82|bash install.sh --target claude --mode copy
    83|bash install.sh --target codex
    84|bash install.sh --target all --dry-run
    85|bash install.sh -h
    86|```
    87|
    88|`--target` 参数可指定为 `cursor`、`claude`、`codex` 或 `all`（默认为 `all`）。`--mode` 参数可指定为 `link`（默认）或 `copy`。`--dry-run` 标志仅打印执行计划而不写入文件。第二次 link 安装会保持正确的符号链接不变。请开启新会话以重新加载技能。路径支持 `$HOME`。
    89|
    90|运行本仓库的测试：
    91|
    92|```bash
    93|python3 -m pytest
    94|```
````

### What is needed (README zh)

Same facts as en. Complete Chinese block, sentence-aligned with en. Same mandatory `~/.codex/skills` manual-cleanup sentence and uninstall-scope sentence.

---

## Current `install.sh` `-h` text (verbatim, stale)

The `usage()` heredoc at `install.sh:5-28` is **unchanged from before this PR** and does **not** match the code that follows it.

````
Usage: install.sh [options]

Link or copy each skills/<name> directory that contains SKILL.md.

Options:
  --target <cursor|claude|codex|all>  Tool skill directory (default: all)
  --mode <copy|link>                  Copy files or create symlinks (default: link)
  --dry-run                           Print the plan and write nothing
  -h, --help                          Show this help

Copy mode also copies shared/ to <name>/shared in each destination.
Link mode reaches shared/ through the symlink target (the repo root).

Destinations are under $HOME:
  cursor  ~/.cursor/skills/<name>
  claude  ~/.claude/skills/<name>
  codex   ~/.codex/skills/<name>

Running the same link install again leaves correct symlinks unchanged.
A copy install replaces the contents of each destination skill directory.
````

### What the help must gain (from code)

1. `--target` line: accept `agents`; state that `all` now means `claude` + `agents` (not `cursor`, not a separate `codex` install pass).
2. New `--project DIR` line: install into `DIR/.claude/skills`, `DIR/.agents/skills`, `DIR/.cursor/skills` instead of under `$HOME`; `DIR` must already exist.
3. New `--uninstall` line: removes only symlinks pointing into this repo and copied dirs containing `.lrs-installed`; others are skipped; works with `--dry-run`, `--target`, `--project`.
4. Destinations block: `codex` is now `~/.agents/skills/<name>` (was `~/.codex/skills`); add `agents ~/.agents/skills/<name>`; mention project-scope paths when `--project` is set.
5. Note that copy mode writes a `.lrs-installed` marker file into each copied skill directory.

Shared/ sentences already in the help remain true (`install.sh:283-286` copy; link reaches shared via the symlink target).

---

## CHANGELOG format (verbatim head of `CHANGELOG.md`)

````
     1|# Changelog
     2|
     3|## 0.2.0 - 2026-10-09
     4|
     5|- Narrative reviews can rank the deduplicated library and keep a user-sized core. Records left out are logged as not read. Systematic, scoping, and umbrella reviews still use the full eligibility screen.
     6|- Each original figure or table is written as an editable SVG plus a PDF. Fig. 1 stays an argument map. Published figures are not cropped.
     ...
    11|## 0.1.0 - 2026-10-09
````

Style: `# Changelog`, then `## X.Y.Z - YYYY-MM-DD`, then hyphen bullets. No `## Unreleased` section exists today. Add a new top section (Unreleased or a new version date) with ASCII hyphen bullets. English only.

### CHANGELOG content that must be covered

- **Changed:** `codex` target destination is `~/.agents/skills` (no longer `~/.codex/skills`); `all` installs `claude` + `agents` only.
- **Added:** `agents` target; `--project DIR`; `--uninstall`; `.lrs-installed` marker written in copy mode.
- **One sentence:** old `~/.codex/skills` is not auto-cleaned; user may delete by hand.

---

## Verified facts from `install.sh` and `tests/test_install.py`

Citations are `file:line` on HEAD `d7ec2b5`.

### Defaults and flags

| Item | Value | Source |
|---|---|---|
| `TARGET` default | `all` | `install.sh:30` |
| `MODE` default | `link` | `install.sh:31` |
| `DRY_RUN` default | `0` | `install.sh:32` |
| `UNINSTALL` default | `0` | `install.sh:33` |
| `PROJECT` default | empty | `install.sh:34` |
| Marker name | `.lrs-installed` | `install.sh:35` (`MARKER=".lrs-installed"`) |
| Accepted `--target` | `cursor`, `claude`, `codex`, `agents`, `all` | `install.sh:95-100` |
| Accepted `--mode` | `copy`, `link` | `install.sh:103-108` |
| New flags parsed | `--uninstall`, `--project` / `--project=` | `install.sh:71-86` |

### Destination roots

`dest_root_for` (`install.sh:136-142`):

- `cursor` → `${BASE}/.cursor/skills`
- `claude` → `${BASE}/.claude/skills`
- `codex` → `${BASE}/.agents/skills`  (**same path as agents**)
- `agents` → `${BASE}/.agents/skills`

`BASE` (`install.sh:111-120`):

- If `--project DIR` is set: `DIR` must be an existing directory (`install.sh:112-114`); then `BASE` is the absolute path of `DIR`.
- Else `BASE="$HOME"`.

User-scope paths therefore:

- Cursor: `~/.cursor/skills/<name>`
- Claude Code: `~/.claude/skills/<name>`
- Codex: `~/.agents/skills/<name>`
- agents: `~/.agents/skills/<name>`

Project-scope paths (`--project DIR`):

- `DIR/.cursor/skills/<name>`
- `DIR/.claude/skills/<name>`
- `DIR/.agents/skills/<name>` (for both `codex` and `agents`)

Tests encode the same map (`tests/test_install.py:61-67`):

```
TARGET_DIRS = {
    "claude": [".claude/skills"],
    "codex": [".agents/skills"],
    "cursor": [".cursor/skills"],
    "agents": [".agents/skills"],
    "all": [".claude/skills", ".agents/skills"],
}
```

`ALL_DIRS` still lists `.codex/skills` only to assert it stays **absent** after install (`tests/test_install.py:68`, `:94-95`).

### What `all` installs

`install.sh:144-149`: when `TARGET == all`, `tools=(claude agents)`. Not `cursor`. Not a separate `codex` pass (and `codex` would have written the same `.agents/skills` tree as `agents` anyway).

### Why `all` drops `cursor` (rationale status)

`/workspace/litreview-pr2-prose-needed.md` states the reason as: Cursor reads both `~/.claude/skills` and `~/.agents/skills`, so installing into both plus `~/.cursor/skills` would duplicate listings. **That Cursor dual-read claim is not stated anywhere in `install.sh` or the tests.** Only the behavioural fact `all → claude + agents` is verified in code. If the writer mentions the Cursor reason, treat it as a product note supplied by the task list, not as something proven by this repo's scripts.

### Copy mode marker

`install.sh:287`: after copying skill files and `shared/`, copy mode runs `printf '%s\n' "$src" > "$dest/$MARKER"`, so each copied skill dir contains a file named `.lrs-installed` whose contents are the source skill path. Tests assert the file exists (`tests/test_install.py:92`).

### `--uninstall` behaviour

Block at `install.sh:186-230`:

1. Iterates the same `tools` list as install (so `--target` and the `all` → `claude`+`agents` rule apply). Honors `--project` via `BASE`. Honors `--dry-run` (`would remove link|copy`).
2. For each expected `dest`:
   - If symlink: remove only when `readlink "$dest"` equals this repo's `$src`; otherwise `skip ... (symlink not created by this repo)` (`install.sh:193-196`).
   - If directory: remove only when `$dest/.lrs-installed` exists; otherwise `skip ... (no .lrs-installed marker)` (`install.sh:205-208`).
   - Else if some other file: skip; if missing: `absent`.
3. Does **not** reference `~/.codex/skills` or `.codex` at all. Old Codex path is never scanned.

Tests:

- Round-trip install then uninstall for every target/mode/user|project scope (`tests/test_install.py:119-146`).
- Foreign unmarked directory, foreign symlink, and unrelated dir are left in place; stdout contains `skip` (`tests/test_install.py:149-163`).
- Second uninstall is a no-op (`tests/test_install.py:146`).
- `--project` with a missing directory exits 1 and writes nothing (`tests/test_install.py:172-175`).

### PR #1-era unmarked copies

Any copy directory without `.lrs-installed` is skipped (`install.sh:206-208`). The marker was introduced on this branch (`01e3a66`); earlier copy installs have no marker, so `--uninstall` will not remove them. User must re-run a copy install (which writes the marker) or delete those directories manually. This matches the task list.

### Old `~/.codex/skills` not auto-cleaned

Confirmed:

- Current install never writes under `.codex/skills` (`dest_root_for` and tests).
- Current uninstall never looks under `.codex/skills`.
- Therefore leftovers from older installs remain until the user deletes them by hand.

### Unchanged behaviours still true

- Link install is idempotent for correct symlinks (`install.sh:243-247`).
- Copy install replaces destination skill contents and also copies `shared/` into `<dest>/shared` (`install.sh:280-286`).
- Link mode does not copy `shared/`; it is reached through the symlink target (`install.sh` help lines still accurate; link branch has no shared copy).
- `--dry-run` prints the plan and writes nothing (install and uninstall).

---

## Contradictions / nuances vs GitHub's stated facts

1. **Aligned:** Codex path is now `~/.agents/skills`. Marker name is `.lrs-installed`. `--uninstall` only removes this repo's symlinks and marker-tagged copies. PR #1-era unmarked copies are skipped. Old `~/.codex/skills` is not auto-cleaned.
2. **Aligned with nuance:** GitHub said `all` = claude + agents (no cursor, no codex). Code: `tools=(claude agents)`. The `codex` *target name* still exists and installs to the same `.agents/skills` path as `agents`; `all` simply does not schedule a third pass under the name `codex`.
3. **Unverified in repo code:** The reason "Cursor reads both `~/.claude/skills` and `~/.agents/skills`" appears only in `litreview-pr2-prose-needed.md`, not in `install.sh` or tests. Behaviour of `all` is verified; the Cursor dual-read explanation is not.
4. **Stale docs on the branch tip:** README table still shows Codex → `~/.codex/skills`; help still lists `--target <cursor|claude|codex|all>` and `codex ~/.codex/skills/<name>`; no `--project` / `--uninstall` / `agents` in help. That staleness is why this writing pass exists, not a code contradiction.
5. **CHANGELOG:** no Unreleased section yet; PR #1 install/shared/CI prose may also be absent from this file on this branch. This PR's entry should cover the install-target changes listed above and must include the manual `~/.codex/skills` cleanup sentence.

