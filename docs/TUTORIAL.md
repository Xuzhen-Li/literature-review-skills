# Getting started with literature-review-skills for beginners

A skill is an instruction pack for each review stage. The AI assistant follows it to walk you step by step from topic to submission. It stops and waits for your confirmation at human gates. It never invents citations. See the Skills table in the README for all 17 skills.

Choose your route:

Cursor users read section 1.

ChatGPT users read section 2.

DeepSeek users read section 3.

Success means seeing the assistant's opening line and having the `project.yaml` file created.

## 0. Preparation

- Downloading and installing the Cursor app [to verify]
- Installing Python on your computer [to verify]
- Finding the button to create a custom GPT in ChatGPT [to verify]
- Finding the DeepSeek website address and its file upload size limit [to verify]
- Running all commands smoothly on Windows [to verify]
- Updating the repository to a newer version: see the FAQ.
- Opening the database homepage when chatting in ChatGPT or DeepSeek [to verify]

You need to open a terminal, which is a text window where you type commands. On macOS, open Applications, then Utilities, then Terminal, or press Command+Space and search for Terminal. On Windows, use Git Bash if Git for Windows is installed, or PowerShell only if `bash` is already on PATH.

Run the following commands to download this repository:

```bash
cd ~
```

```bash
git clone https://github.com/Xuzhen-Li/literature-review-skills
```

![01-git-clone](tutorial/img/01-git-clone.png)

[screenshot to add] terminal-open-mac

[screenshot to add] terminal-open-windows

Enter the newly downloaded folder. All future commands are run here:

```bash
cd literature-review-skills
```

## 1. Using it in Cursor

First, download and install Cursor itself. Run the installation script:

```bash
bash install.sh --target cursor
```

A successful terminal installation shows 17 `linked` lines and ends with `finished: 17 action(s) processed`.

![02-install-cursor](tutorial/img/02-install-cursor.png)

Running `ls ~/.cursor/skills` lists the 17 installed skill folders (shown in the top half of the screenshot).

![04-ls-installed](tutorial/img/04-ls-installed.png)

Start a new session so Cursor reloads the skills. Whether Cursor shows a loaded indicator is [to verify].

The repository includes a Cursor rule to help the assistant choose the right skill. It does not apply every time, only when relevant. With Cursor, you do not need the bundling steps in section 2. This route needs no bundle file.

Type this in the chat to begin:

```
start a new review on drought responses in grapevine
```

[screenshot to add] cursor-new-chat

In chat, the assistant gives its opening line, then opens the database homepage.

[screenshot to add] cursor-first-reply

## 2. Using it in ChatGPT

You must first install Python. Open your terminal in the repository root and generate the bundle, which is a single package containing all required instructions and files for chat platforms:

```bash
python3 scripts/bundle.py
```

The generated files are in the `dist/` folder. You must run the command above to generate this folder; it is not included in the downloaded repository. A successful build ends with `knowledge files: 18 (max 20)`.

[screenshot to add] chatgpt-bundle-terminal

Open ChatGPT and create or edit a custom GPT (button location is [to verify]). Paste all of `dist/chatgpt/instructions.md` into the Instructions box.

[screenshot to add] chatgpt-gpt-instructions

Upload all 18 files from `dist/chatgpt/knowledge/` as Knowledge. A knowledge file is a reference document the AI reads to understand the skills.

[screenshot to add] chatgpt-dist-folder

[screenshot to add] chatgpt-gpt-knowledge

In chat, the GPT asks you to paste or attach `project.yaml` and `LOG.md`, or routes to project setup if they do not exist.

[screenshot to add] chatgpt-first-reply

Note: Custom GPTs on the Enterprise plan are retiring on 2026-12-11. After that, please switch to the Cursor or DeepSeek route.

Note: Chat platforms cannot run scripts.

## 3. Using it in DeepSeek

Build the files the same way as section 2 to get `dist/deepseek/literature-review-skills.md`. Open the DeepSeek chat page and start a new chat (URL and buttons are [to verify]). Paste the whole file as the first message, or attach it. We cannot promise whether the web version keeps a system prompt or what its upload limit is. API users can put the file in the system message.

[screenshot to add] deepseek-attach

After your question, the assistant judges the stage and asks for `project.yaml` and `LOG.md` when needed.

[screenshot to add] deepseek-first-reply

## 4. Minimal example

Start by typing this first message:

```
start a new review on drought responses in grapevine
```

This triggers `review-project-setup`. The assistant gives a fixed opening line. It opens the Web of Science homepage and lets you sign in, but it never types your password. On chat platforms, you may need to open the database homepage in your browser yourself, then reply with the fixed sentence.

You hit a gate, which is a built-in pause where the AI waits for your explicit approval before continuing. You must reply with one exact line:

```
I have confirmed institutional login
```

Or:

```
I have no download permission on this computer
```

Replying with just yes or ok does not count; you must copy the exact sentence above.

Next, the assistant will ask you 8 things in one message: title, field, review type, audience, timeline, target journal, whether PubMed will be searched, and the project folder path. After you answer, it creates the project folder, plus the `project.yaml` and `LOG.md` files.

[screenshot to add] example-project-yaml

Next message:

```
what is the next step
```

The `review-orchestrator` reports the stage.

[screenshot to add] example-next-step

There are 7 human gates in total. At a gate, the assistant stops and waits for you to type a fixed sentence before continuing, for example:

```
I confirm the topic lock
```

On ChatGPT or DeepSeek, you keep `project.yaml` and `LOG.md` yourself and paste them back next time.

## 5. FAQ

### What is the difference between a skill and a plugin? Which should I use?

The 17 skills are the same, but the plugin route puts the whole repository (including `.cursor/rules`, `scripts`, `platform`, `plugin.json`) into `~/.cursor/plugins/local/`, and whether Cursor picks up `skills/` from the plugin route is [to verify]. [[TODO-TEXT]] We recommend using skills (installed to `~/.cursor/skills`). The local plugin is a backup Route B.

### I have no programming experience. Do I have to use a terminal?

Yes, but you only need to copy and paste a few commands.

### `bash install.sh` says `exists and is not a symlink`. What do I do?

The installation destination exists as a real folder, not a symlink (a shortcut that points to the repo folder). You must remove the old folder first, then install again. Run `--uninstall` for your target, or delete a hand-copied folder by hand because it lacks the `.lrs-installed` marker.

### I installed it, but the assistant does not seem to use the skills. Why?

Start a new session so the platform reloads the skills.

### Where is the `dist/` folder? Why is it not in the download?

It is not in the repository. You must generate it locally by running `python3 scripts/bundle.py` in the repository root.

### ChatGPT says the instructions are too long or there are too many files. What now?

Paste only `instructions.md` into the Instructions box. Upload the 18 knowledge files as attached files. The limits are 8,000 characters for instructions and 20 knowledge files. If files are stale, rebuild them by running `python3 scripts/bundle.py` in the repository root.

### Will this still work after custom GPTs are retired?

Custom GPTs on the Enterprise plan are retiring on 2026-12-11. After that, please switch to the Cursor or DeepSeek route.

### How large a file can I upload to DeepSeek on the web?

The upload limit is [to verify].

### Can the chat run the deduplication script?

No, chat platforms cannot run scripts.

### Will the assistant invent references for me? Will it submit for me?

No, it never invents citations and stops at human gates.

### What is a human gate, and why must I reply with a fixed sentence?

It is a stopping point requiring a fixed sentence because simple words like "yes" or "ok" do not count.

### If I open a new chat, do I lose my progress?

Keep `project.yaml` and `LOG.md` yourself and paste them back next time.

### Does it work on Windows?

Use Git Bash if Git for Windows is installed, or PowerShell only if `bash` is already on PATH. If `python3` is not found, try `python` or `py` instead.

### How do I update to a new version?

Run `git pull` then run the `install.sh` script again; a rerun prints `unchanged  link ...` instead of linked, and this is normal.

### How do I uninstall?

Run these commands (if you installed only cursor, you only need `bash install.sh --target cursor --uninstall`; the agents command is only needed if agents was installed, but running it anyway is harmless and shows 0 removal(s)):

```bash
bash install.sh --target cursor --uninstall
```

```bash
bash install.sh --target agents --uninstall
```

![05-uninstall](tutorial/img/05-uninstall.png)

![06-ls-after-uninstall](tutorial/img/06-ls-after-uninstall.png)

If you installed an older version before, the old `~/.codex/skills` is not cleaned automatically; delete it by hand.

## 6. Advanced installation

Other ways:

For Route B, local plugins must be cloned or copied directly to `$HOME/.cursor/plugins/local/literature-review-skills` because symlinks are not allowed there.

`--target agents` installs to `~/.agents/skills`, which Codex reads.

![03-install-agents](tutorial/img/03-install-agents.png)

`--target all` installs cursor, claude and agents at once.

Add `--dry-run` to show the plan and write nothing.
