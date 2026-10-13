# Platform bundles

This directory holds templates and budgets for paste-ready chat bundles. The `scripts/bundle.py` script builds ChatGPT custom GPT files and one DeepSeek long-context file into `dist/`. Because `dist/` is in `.gitignore` and not committed, regenerate it with the Build commands below. Open a terminal in the repo root (which contains `scripts/` and `platform/`), then run the build command.

## Build

```bash
python3 scripts/bundle.py            # writes dist/chatgpt/ and dist/deepseek/
python3 scripts/bundle.py --check    # build in a temp dir, check limits only
```

## ChatGPT (custom GPT)

After running the build, open ChatGPT to create or edit a custom GPT. Paste the text from `dist/chatgpt/instructions.md` into the Instructions box. Upload all 18 files from `dist/chatgpt/knowledge/` as knowledge. Be aware of platform limits: instructions cap at 8,000 characters (the build ensures under 7,500) and at most 20 knowledge files are allowed. Custom GPTs are currently being retired, with Enterprise retirement planned for 2026-12-11. Use this route while custom GPTs remain available, though it is not a permanent long-term ChatGPT home.

Files:

- `dist/chatgpt/instructions.md`
- `dist/chatgpt/knowledge/*.md`

## DeepSeek (single long-context file)

After building, use `dist/deepseek/literature-review-skills.md` as your first message paste or as an attachment in a DeepSeek chat. For API calls, provide it as the system message. DeepSeek API documentation supports a 1M token context. However, web UI system-prompt persistence and exact file upload limits are unverified, so avoid relying on a specific web upload number.

File:

- `dist/deepseek/literature-review-skills.md`

## Limits checked by the build

| Product | Limit | Source |
|---|---|---|
| `dist/chatgpt/instructions.md` | 8,000 characters (projected ≤ 7,500) | https://help.openai.com/en/articles/8554397-creating-and-editing-gpts |
| `dist/chatgpt/knowledge/` | at most 20 files | https://help.openai.com/en/articles/8554397-creating-and-editing-gpts |
| `dist/deepseek/literature-review-skills.md` | 400,000 characters | https://api-docs.deepseek.com/quick_start/pricing |

`scripts/bundle.py` exits with status 1 if hard limits are exceeded, projected instructions exceed 7,500 characters, knowledge files exceed 20, or a placeholder is missing from `platform/budgets.json`. The projected size is the raw text plus each slot's budget. To raise a slot's allowance, edit `platform/budgets.json` and run:
```
python3 scripts/bundle.py --check
```
