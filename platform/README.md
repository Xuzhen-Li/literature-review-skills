# Platform bundles

[[TODO-TEXT:pf-readme-intro]]

## Build

```bash
python3 scripts/bundle.py            # writes dist/chatgpt/ and dist/deepseek/
python3 scripts/bundle.py --check    # build in a temp dir, check limits only
```

## ChatGPT (custom GPT)

[[TODO-TEXT:pf-readme-chatgpt]]

Files:

- `dist/chatgpt/instructions.md`
- `dist/chatgpt/knowledge/*.md`

## DeepSeek (single long-context file)

[[TODO-TEXT:pf-readme-deepseek]]

File:

- `dist/deepseek/literature-review-skills.md`

## Limits checked by the build

| Product | Limit | Source |
|---|---|---|
| `dist/chatgpt/instructions.md` | 8,000 characters (projected ≤ 7,500) | https://help.openai.com/en/articles/8554397-creating-and-editing-gpts |
| `dist/chatgpt/knowledge/` | at most 20 files | https://help.openai.com/en/articles/8554397-creating-and-editing-gpts |
| `dist/deepseek/literature-review-skills.md` | 400,000 characters | https://api-docs.deepseek.com/quick_start/pricing |

[[TODO-TEXT:pf-readme-limits-note]]
