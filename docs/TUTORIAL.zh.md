# literature-review-skills 新手教程

skill 是写综述每个阶段的说明书。AI 助手照着它，带你从选题一步步走到投稿。遇到人工关卡会停下等你确认。它不会编造文献。详细内容请见 README 的 Skills 表。

请选择你的路线：

Cursor 用户请看第 1 节。

ChatGPT 用户请看第 2 节。

DeepSeek 用户请看第 3 节。

跑通 = 看到助手开场白并建好 `project.yaml`。

## 0. 准备

- 下载并安装 Cursor 软件【待核实】
- 在电脑上安装 Python【待核实】
- 在 ChatGPT 里找到新建 custom GPT 的按钮位置【待核实】
- DeepSeek 网页端网址以及文件上传大小限制【待核实】
- 在 Windows 电脑上运行全部命令的支持情况【待核实】
- 将仓库更新到新版本的方法【待核实】
- 在 ChatGPT 或 DeepSeek 对话中打开数据库主页的操作方式【待核实】

打开终端（输入命令的窗口，macOS 按 Command+空格，输入“终端”，回车；Windows 装了 Git for Windows 就用 Git Bash，只有 `bash` 已在 PATH 上时才用 PowerShell）。

先回到个人主目录，再下载本仓库：

```bash
cd ~
```

```bash
git clone https://github.com/Xuzhen-Li/literature-review-skills
```

![01-git-clone](tutorial/img/01-git-clone.png)

[截图待补] terminal-open-mac

[截图待补] terminal-open-windows

下载完成后，进入刚下载的文件夹：

```bash
cd literature-review-skills
```

以后的命令都在这里运行。

## 1. 在 Cursor 里用

首先下载并安装 Cursor 本身。运行以下安装命令：

```bash
bash install.sh --target cursor
```

终端的成功输出会有 17 行 `linked`，最后一行是 `finished: 17 action(s) processed`。

![02-install-cursor](tutorial/img/02-install-cursor.png)

运行 `ls ~/.cursor/skills` 检查，应看到 17 个 skill 文件夹名（图中只需看 Cursor 那部分）。

![04-ls-installed](tutorial/img/04-ls-installed.png)

装完开一个新对话，让 Cursor 重新加载 skill。Cursor 界面里有没有 skill 已加载的标志【待核实】。

仓库里自带一条 Cursor 规则，会帮助助手选对 skill。它不会每次都启用，只在相关时生效。用 Cursor 不需要下面第 2 节的打包步骤。

在对话框里输入：

```
start a new review on drought responses in grapevine
```

[截图待补] cursor-new-chat

对话里，助手先说开场白，然后去打开数据库主页。

[截图待补] cursor-first-reply

## 2. 在 ChatGPT 里用

需要先装 Python。在仓库根目录运行以下命令生成 bundle（打包好的单一文件）：

```bash
python3 scripts/bundle.py
```

生成的文件在 `dist/` 文件夹里。这个文件夹要你自己运行上面的命令生成，下载的仓库里没有。构建成功最后一行是 `knowledge files: 18 (max 20)`。

[截图待补] chatgpt-bundle-terminal

打开 ChatGPT，新建或编辑一个 custom GPT（入口位置【待核实】）。把 `dist/chatgpt/instructions.md` 全文粘进 Instructions 框。

[截图待补] chatgpt-gpt-instructions

把 `dist/chatgpt/knowledge/` 里的 18 个文件全部上传为 Knowledge。knowledge 文件是让 AI 阅读以理解 skill 的参考文档。

[截图待补] chatgpt-dist-folder

[截图待补] chatgpt-gpt-knowledge

对话里，GPT 会请你粘贴或附上 `project.yaml` 和 `LOG.md`；如果还没有，就转到建项目那一步。

[截图待补] chatgpt-first-reply

注意：Enterprise 计划的 custom GPT 将于 2026-12-11 停用。之后请改用 Cursor 或 DeepSeek 路线。

注意：聊天里不能运行脚本。

## 3. 在 DeepSeek 里用

构建步骤同第 2 节，文件是 `dist/deepseek/literature-review-skills.md`。打开 DeepSeek 聊天页，新开一个对话（网址和按钮【待核实】）。把整个文件作为第一条消息粘贴，或作为附件上传。网页端有没有持久的系统提示、上传上限多少。API 用户把文件放进 system 消息。

[截图待补] deepseek-attach

发出问题后，助手判断当前阶段；需要时请你粘贴 `project.yaml` 和 `LOG.md`。

[截图待补] deepseek-first-reply

## 4. 最小示例

首先输入第一条消息：

```
start a new review on drought responses in grapevine
```

这会触发 `review-project-setup`。助手说完开场白，会打开 Web of Science 主页，请你登录。助手不会替你输密码。在聊天平台上，可能要你自己在浏览器里打开数据库主页，再回固定句子（此步【待核实】）。

你遇到了人工关卡（gate），这是要求打出特定文字确认后才会放行的节点。你必须回一句固定的话：

```
I have confirmed institutional login
```

或：

```
I have no download permission on this computer
```

只回 yes 或 ok 不算数，要照抄上面的整句。

接着，助手会在一条消息里问你 8 件事：标题；研究领域；综述类型；目标读者；时间安排；目标期刊；是否检索 PubMed；项目文件夹放哪。你答完后，它会建好项目文件夹，以及 `project.yaml` 和 `LOG.md` 两个文件。

[截图待补] example-project-yaml

下一句：

```
what is the next step
```

由 `review-orchestrator` 报告阶段。

[截图待补] example-next-step

全程共有 7 个人工关卡。到了关卡，助手会停下，等你打出一句固定的话才继续，例如：

```
I confirm the topic lock
```

在聊天平台（ChatGPT/DeepSeek）上，要你自己保存 `project.yaml` 和 `LOG.md`，下次再贴回去。

## 5. FAQ

### skill 和插件有什么区别？我该用哪一种？

两者装的内容一样，只是位置不同。推荐用 skill（装到 `~/.cursor/skills`）。本地插件是备用的路线 B。

### 我没有编程经验，必须用终端吗？

需要，但只要复制粘贴几条命令。

### 运行 `bash install.sh` 报错 `exists and is not a symlink` 怎么办？

安装目标是一个真正的文件夹，而不是符号链接（指向仓库文件夹的快捷方式）。你必须先删除旧文件夹，然后再安装。运行 `--uninstall` 卸载你的目标，或者手动删除你手动复制的文件夹，因为它没有 `.lrs-installed` 标记。

### 装完了，助手好像没用上 skill，怎么办？

装完后需要开一个新会话，让 Cursor 重新加载 skill。

### `dist/` 文件夹在哪里？为什么下载的仓库里找不到？

`dist/` 不在仓库里，要自己在根目录运行 `python3 scripts/bundle.py` 生成。

### ChatGPT 提示指令太长或文件太多怎么办？

只把 `instructions.md` 粘贴到 Instructions 框中。把 18 个 knowledge 文件作为文件附件上传。指令最多 8,000 字符，知识文件最多 20 个。如果文件过时，请在根目录重新运行 `python3 scripts/bundle.py` 生成最新文件。

### custom GPT 退役以后还能用吗？

Enterprise 计划的 custom GPT 将于 2026-12-11 停用。之后请改用 Cursor 或 DeepSeek 路线。

### DeepSeek 网页端能上传多大的文件？

上传上限【待核实】。

### 聊天里能运行去重脚本吗？

不能，聊天里不能运行脚本。

### 助手会帮我编参考文献吗？会替我投稿吗？

不会，助手不会编造文献，遇到人工关卡会停下等你确认。

### 什么是人工关卡（gate）？为什么要我回一句固定的话？

它是要求打出特定文字确认后才会放行的节点，只回 yes 或 ok 不算数。

### 下次打开新对话，之前的进度会丢吗？

在聊天平台上，要你自己保存 `project.yaml` 和 `LOG.md`，下次再贴回去。

### Windows 上能用吗？

装了 Git for Windows 就用 Git Bash；只有 `bash` 已在 PATH 上时才用 PowerShell。如果找不到 `python3`，请尝试使用 `python` 或 `py`。

### 怎么更新到新版本？

运行 `git pull` 后重新运行 `install.sh` 脚本。

### 怎么卸载？

运行以下命令：

```bash
bash install.sh --target cursor --uninstall
```

```bash
bash install.sh --target agents --uninstall
```

![05-uninstall](tutorial/img/05-uninstall.png)

![06-ls-after-uninstall](tutorial/img/06-ls-after-uninstall.png)

如果你以前装过旧版，`~/.codex/skills` 不会自动删除，需要手动删掉。

## 6. 进阶安装

其他方式：

本地插件路线 B 必须直接克隆或复制到 `$HOME/.cursor/plugins/local/literature-review-skills`，不能用符号链接。

Codex 用 `--target agents` 装到 `~/.agents/skills`。

![03-install-agents](tutorial/img/03-install-agents.png)

`--target all` 一次装三处（cursor、claude、agents）。

想先看计划不写文件，加 `--dry-run`。
