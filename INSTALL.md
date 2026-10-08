# 下载这个 Skill，帮用户做逐句精听

这份文档供智能体与初次使用者阅读。仓库地址：

https://github.com/yb-beep/listening-sentence-index

## 复制给智能体就行

> 请帮我安装这个四六级逐句精听 Skill：https://github.com/yb-beep/listening-sentence-index 。优先使用我提供的安装包，否则从仓库下载；按包内说明准备好环境；如果我还没提供音频，请提醒我提供。收到音频后，生成带英文原文和中文译文的单文件精听网页，抽查句首句尾，自动打开成品，并在桌面创建「四六级逐句精听」快捷方式，让我以后双击就能练。最后简单告诉我：怎么开始练，以及下次换音频时该发什么话。

发给 WorkBuddy、豆包工作或 Codex，再提供音频；有原文也一起给。以下内容是给智能体读取的下载与运行指南，读者不必先学 Git 或 Python 命令。

## 给智能体：下载与安装

用户明确要求安装或使用本工具时，先识别所在平台、可用文件权限、终端与 Python 环境。不要假设普通网页聊天拥有本地执行能力。

如果用户已经提供 Skill 压缩包，优先直接解压该包并阅读 `SKILL.md`；GitHub 无法访问时也可按此方式安装。包内 `scripts/` 已包含修复后的源码，无需另行应用补丁。

没有本地安装包时，取得完整目录，任选可用方式：

- 克隆 `https://github.com/yb-beep/listening-sentence-index.git`。
- 下载 Release：`https://github.com/yb-beep/listening-sentence-index/releases/latest/download/listening-sentence-index-skill.zip`，解压保留顶层文件夹。
- 若 Release 暂不可用，下载仓库 main 分支 ZIP：`https://github.com/yb-beep/listening-sentence-index/archive/refs/heads/main.zip`。

保留 `SKILL.md`、`scripts/`、`references/` 的相对结构。检查已有同名 Skill；如已有用户修改，先保留副本，避免直接覆盖。

### WorkBuddy

优先使用客户端的本地技能包导入机制，技能页支持上传技能。作者本机使用的目录为 `~/.workbuddy/skills/listening-sentence-index/`；复制文件时需确认当前版本也从该目录发现技能，或改用客户端导入并启用。

确认能够读取 Skill。读 `SKILL.md`，按用户指定工作目录处理材料；环境依赖不要安装到未知的受保护系统 Python，必要时使用虚拟环境。

### 豆包工作

使用具备技能导入或本地脚本执行能力的工作任务环境。先读取仓库，检查当前客户端支持的技能加载方式，再安装完整包。不要猜测豆包工作的技能目录或将普通聊天等同于工作任务；若缺少必要执行能力，直接说明缺项，让用户选择 WorkBuddy 的桌面流程。

### Codex

本地用户 Skill 可以放在 `~/.agents/skills/listening-sentence-index/`。确认发现并读取后，使用能访问用户文件和运行脚本的环境制作。不要替用户改变其他 Skill 或无关配置。

## 开始制作

读取 `SKILL.md`，检查依赖。用户没有音频时，等待用户提供；没有原文可做自动转写，但需要检查。用户要求中文时，另行逐句翻译，写入与最终序号对应的译文，再生成页面。

默认先用短材料确认流程。保留转写、对齐、补漏、切分、翻译与生成的正确顺序。完成后检查页面并抽听相邻句子，按下一节打开成品、创建快捷方式，报告检查范围、成品路径与练习方法。

## 来源与检查范围

WorkBuddy 导入方式：[官方技能说明](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。Codex 本地发现路径：[OpenAI 官方 Build skills](https://learn.chatgpt.com/docs/build-skills)。

豆包工作被列为用户希望使用的入口，尚未在本次发布中完成技能安装与整套音频制作验收，因此指引要求先检查客户端能力。这里只提供三种入口，不包含其他智能体。

## 交付后打开与桌面入口

用户提示词已经要求打开成品、创建桌面快捷方式，按此完成交付。Skill 是制作流程，桌面入口指向生成的单文件 HTML。

- 将成品保存在稳定的用户工作目录，保留音频和检查记录。不要让快捷方式指向临时下载目录。
- macOS 可创建 `.webloc`，其中 `URL` 为成品的 `file://` URI；Windows 可创建指向成品的 `.lnk` 或 `.url`；Linux 使用合适的桌面入口。识别实际桌面目录，包括系统重定向的桌面，正确处理中文和空格。
- 快捷方式显示名优先用「四六级逐句精听」。已有同名入口时保留旧材料，避免误删用户文件。
- 打开成品并确认入口确实能到达可用页面；不只创建一个空图标。若当前智能体不能操作桌面，直接说明限制并给可直接打开的成品路径。
- 最后只告诉初次使用者三个要点：成品位置；双击图标后点一句播放；下次把新音频交给智能体并说“用这个 Skill 做新的精听材料”。

制作其他音频仍由智能体处理；桌面入口用于打开已制作的材料。
