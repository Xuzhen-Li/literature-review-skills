# 面向新手的 literature-review-skills 上手教程
skill 是每个综述阶段的一份说明书，让 AI 助手一步步带你从选题走到投稿，在人工关卡处停下，不编造文献。详细内容请见 README 的 Skills 表。

## 1. 在 Cursor 里用

安装 Cursor 本身：待核实。获取本仓库：在终端（输入电脑命令的文本窗口，macOS 用终端，Windows 装了 Git for Windows 就用 Git Bash，只有 `bash` 已在 PATH 上时才用 PowerShell）里输入命令。

```bash
git clone https://github.com/Xuzhen-Li/literature-review-skills
```

进入克隆下来的文件夹，运行安装命令。

```bash
bash install.sh --target cursor
```

会装到 `~/.cursor/skills/<name>`。装完开一个新会话，让 Cursor 重新加载 skill。在 Cursor 里打开本仓库文件夹时，`.cursor/rules/literature-review.mdc` 会帮助路由；它的 `alwaysApply: false`。

其他方式：路线 B，本地插件必须直接克隆或复制到 `$HOME/.cursor/plugins/local/literature-review-skills`，不能用符号链接。`--target agents` 装到 `~/.agents/skills`，Codex 读这个位置。`--target all` 会装 cursor、claude、agents 三处。想先看计划不写文件，加 `--dry-run`。

Cursor 路线不需要 bundle（打包好的单一文件）文件。在对话框里输入：

```
start a new review on drought responses in grapevine
```

终端里有 17 行 `linked … -> …`，最后一行是 `finished: 17 action(s) processed`。
![02-install-cursor](tutorial/img/02-install-cursor.png)
用 `ls ~/.cursor/skills` 检查，能看到 17 个 skill 文件夹名。
![04-ls-installed](tutorial/img/04-ls-installed.png)（只看 Cursor 部分）
如果也装了 agents：![03-install-agents](tutorial/img/03-install-agents.png)
对话里，助手先说开场白，然后去打开数据库主页。Cursor 界面里有没有 skill 已加载的标志：待核实。
[截图待补] cursor-new-chat
[截图待补] cursor-first-reply

## 2. 在 ChatGPT 里用

先在仓库根目录运行构建。

```bash
python3 scripts/bundle.py
```

产物在 `dist/`。`dist/` 不在仓库里，要自己生成【待定】。需要先装 Python：待核实。打开 ChatGPT，新建或编辑一个 custom GPT：入口位置待核实。

把 `dist/chatgpt/instructions.md` 全文粘进 Instructions 框。把 `dist/chatgpt/knowledge/` 里的 18 个文件全部上传为 Knowledge。上限：指令最多 8,000 字符，知识文件最多 20 个。

构建终端最后一行是 `knowledge files: 18 (max 20)`。对话里，GPT 会请你粘贴或附上 `project.yaml` 和 `LOG.md`；如果还没有，就转到建项目那一步。

custom GPT 正在退役（Enterprise 计划 2026-12-11）。聊天里不能运行脚本。
[截图待补] chatgpt-bundle-terminal
[截图待补] chatgpt-dist-folder
[截图待补] chatgpt-gpt-instructions
[截图待补] chatgpt-gpt-knowledge
[截图待补] chatgpt-first-reply

## 3. 在 DeepSeek 里用

构建步骤同第 2 节。文件是 `dist/deepseek/literature-review-skills.md`。打开 DeepSeek 聊天页，新开一个对话：网址和按钮待核实。

把整个文件作为第一条消息粘贴，或作为附件上传。网页端有没有持久的系统提示、上传上限多少，待核实。API 用户把文件放进 system 消息。

发出问题后，助手判断当前阶段；需要时请你粘贴 `project.yaml` 和 `LOG.md`。
[截图待补] deepseek-attach
[截图待补] deepseek-first-reply

## 4. 怎么打开终端

macOS：应用程序，实用工具，终端。
Windows：装了 Git for Windows 就用 Git Bash；只有 `bash` 已在 PATH 上时才用 PowerShell【待定】。
在克隆下来的目录里运行命令。

```bash
cd ~
```

```bash
git clone https://github.com/Xuzhen-Li/literature-review-skills
```

![01-git-clone](tutorial/img/01-git-clone.png)
[截图待补] terminal-open-mac
[截图待补] terminal-open-windows

## 5. 最小示例

```
start a new review on drought responses in grapevine
```

会触发 `review-project-setup`。助手先说固定开场白。然后先打开 Web of Science 主页，请你登录；助手不输入密码。

```
I have confirmed institutional login
```

或

```
I have no download permission on this computer
```

回 yes 或 ok 不算。再在一条消息里问：标题、领域、综述类型、读者、时间线、目标期刊、是否检索 PubMed、项目目录路径。然后建文件夹、`project.yaml` 和 `LOG.md`。

```
what is the next step
```

由 `review-orchestrator` 报告阶段。人工关卡（gate）是要求你打出特定文字确认后才会放行的节点，共 7 个。通过关卡要回一句固定的话。

```
I confirm the topic lock
```

聊天平台（ChatGPT/DeepSeek）上，要你自己保存 `project.yaml` 和 `LOG.md`，下次再贴回去。自己在浏览器里打开主页，再回固定句子：待核实。
[截图待补] example-project-yaml
[截图待补] example-next-step

## 6. FAQ

skill 和插件有什么区别？我该用哪一种？
主线路线使用 skill（安装到 `~/.cursor/skills`），而本地插件是路线 B，建议使用主线。

我没有编程经验，必须用终端吗？
是的，获取本仓库需要用终端运行 `git clone`，安装也需要运行终端命令。

运行 `bash install.sh` 报错 `exists and is not a symlink` 怎么办？
插件目录不能用符号链接，必须直接克隆或复制。

装完了，助手好像没用上 skill，怎么办？
装完后需要开一个新会话，让 Cursor 重新加载 skill。

`dist/` 文件夹在哪里？为什么下载的仓库里找不到？
`dist/` 不在仓库里，要自己在根目录运行 `python3 scripts/bundle.py` 生成。

ChatGPT 提示指令太长或文件太多怎么办？
把 `dist/chatgpt/knowledge/` 里的 18 个文件全部上传。上限：指令最多 8,000 字符，知识文件最多 20 个。

custom GPT 退役以后还能用吗？
custom GPT 正在退役（Enterprise 计划 2026-12-11）。

DeepSeek 网页端能上传多大的文件？
上传上限在仓库中被标为未核实。

聊天里能运行去重脚本吗？
不能，聊天里不能运行脚本。

助手会帮我编参考文献吗？会替我投稿吗？
不会，助手不编造文献，并在人工关卡处停下。

什么是人工关卡（gate）？为什么要我回一句固定的话？
人工关卡共 7 个，通过关卡必须要回一句固定的话，回 yes 或 ok 不算。

下次打开新对话，之前的进度会丢吗？
在聊天平台上，要你自己保存 `project.yaml` 和 `LOG.md`，下次再贴回去。

Windows 上能用吗？【待定】
装了 Git for Windows 就用 Git Bash；只有 `bash` 已在 PATH 上时才用 PowerShell。如果找不到 `python3`，请尝试使用 `python` 或 `py`。

怎么更新到新版本？
更新步骤目前待核实。

怎么卸载？

```bash
bash install.sh --target cursor --uninstall
```

![05-uninstall](tutorial/img/05-uninstall.png)
![06-ls-after-uninstall](tutorial/img/06-ls-after-uninstall.png)
旧的 `~/.codex/skills` 不会被自动清理，需要手动删除。
