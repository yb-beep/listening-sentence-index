---
name: listening-sentence-index
description: 将用户提供的英语听力音频（包括四级、六级）制作成逐句精听材料，支持标准原文对齐、中文译文、单句音频与音频内嵌的单文件 HTML。用户要按句切分、做盲听、逐句听写或生成精听索引时使用。
---

# 英语听力 → 逐句精听网页

用户提供音频，可选配套原文。交付可在电脑浏览器打开的「单文件版 HTML」，同时保留逐句音频、索引与时间轴供修正和二次处理。

## 运行条件

本 Skill 需要文件访问和 Python 脚本执行环境。先确认可访问用户材料与输出目录，再检查依赖。首次需要安装依赖、下载识别模型；不要将其描述为所有平台都无需安装或可一键完成。

```bash
python scripts/prepare.py --install
```

依赖为 `faster-whisper`、`av`、`numpy`。本流水线使用 PyAV 编解码，不依赖外部 ffmpeg 命令。遇到系统 Python 安装限制，使用工作目录中的虚拟环境。

网络或模型下载问题先看 [环境配置](references/env-setup.md)。准备完成后可以在本地做识别；翻译由所用智能体完成，其联网与数据处理方式取决于平台设置。

## 制作流程

工作目录与输入参数第一次写入 `config.json`，后续步骤可只传 `--work`。为用户准备独立工作目录，避免不同材料互相覆盖。

```bash
python scripts/run_all.py --work ./out --audio ./listen.mp3 \
  --ref ./reference.txt --title "四六级听力精听"
```

没有原文时去掉 `--ref`。可用原文时优先提供，自动对齐仍不等于完成了人工校对。

分步顺序为：

```bash
python scripts/transcribe.py --work ./out --audio ./listen.mp3
python scripts/align.py --work ./out --ref ./reference.txt
python scripts/fill_gaps.py --work ./out
python scripts/split.py --work ./out
python scripts/build_index.py --work ./out --title "四六级听力精听"
python scripts/make_single.py --work ./out --title "四六级听力精听"
```

必须先 `align.py` 再 `fill_gaps.py`：前者会重写 `sentences.json`，顺序反过来会覆盖补识别的结果。`sentences.json` 是切分时间轴的事实来源。

## 配中文译文

脚本不会自动调用翻译模型。用户要求中英对照时，由你读 `sentences.json`，按最终句子序号逐句翻译。

1. 每批约 40–60 句，写 `out/_trans_N.json`，形如 `{"1":"中文译文","2":"中文译文"}`。
2. 保持意思准确、简洁，不补充原文没有的信息。
3. 用 `merge_translations.py --work ./out --check` 检查缺项，再合并。
4. 加入译文后重新生成索引与单文件版。

```bash
python scripts/merge_translations.py --work ./out --check
python scripts/merge_translations.py --work ./out
python scripts/build_index.py --work ./out
python scripts/make_single.py --work ./out --restart
```

未配译文时页面仍可用，中文为空。不要把英文自动识别结果或自动对齐标签称为经过人工校对。

## 中断与重新生成

`transcribe.py` 按音频块记进度，可重跑同一条命令接着转写。`split.py` 核对片段边界、源音频与代码更新时间，匹配时复用，变化时重新切分。

完整流水线续跑：

```bash
python scripts/run_all.py --work ./out --resume
```

`--restart` 忽略已有产物或进度，使用前判断是否需要保留用户已有修改。流水线检测到源音频、参考原文或识别设置变化时会重新制作，旧译文保存到 `_previous_inputs/`。仍建议每份材料使用独立目录，避免混用素材。

`run_all.py` 当前只接收它定义的参数；`--limit`、`--jobs`、`--batch-size` 等应传给支持它们的分步脚本。默认识别模型 `large-v3-turbo`，默认并行度 2；处理速度与质量取决于硬件和材料。

## 交付前检查

```bash
node scripts/check_page.js "./out/四六级听力精听（单文件版）.html" <句子数>
```

检查占位符、句子与音频数、主要按钮。安装了 jsdom 时脚本还会检查部分页面交互。人工抽听 5–10 对相邻句子，特别检查句首、句尾、长句和题目：不能截断词，也不能明显串入下一句。

```bash
VERIFY_IDS=1,2,3,40,41 python scripts/verify_clips.py --work ./out
```

自动再识别用于发现可疑片段，不能代替抽听。边界问题看 [调参说明](references/boundary-tuning.md)，修正后重生成音频与页面。页面中的「当前句作起点/终点」只设置连播范围，不能修正音频时间轴。

## 成品功能与交付口径

当前单文件模板支持：默认隐藏原文、单句揭开、循环、0.6/0.75/0.9/1.0/1.2 倍速、句间间隔、区间与分组连播、听写文字比较、星标筛选、浏览器本地记录。

三阶段连播为盲听 → 显示英文复听 → 显示中文后进入下一句，不是自动跟读录音评分。Anki 导出为 ZIP 内的 MP3、CSV 与导入说明，不是 `.apkg`；实际导入需检查字段和音频。

交付时说明单文件版在哪里、如何用电脑浏览器打开，以及做了哪些检查。它内嵌音频，可离线练习；不要保证任意手机、聊天软件预览或浏览器都兼容。学习记录保存在当前浏览器，不自动跨设备同步。

## 桌面入口与初次使用交付

用户要求时，自动打开成品并创建指向单文件 HTML 的桌面快捷方式，显示名「四六级逐句精听」。将成品保存在稳定工作目录，按当前系统创建 `.webloc` / `.lnk` / `.url` 或桌面入口，确认实际桌面路径。不要覆盖用户已有的无关同名文件。入口应指向已生成的练习页；制作新音频由智能体再次运行流程。细节见 [INSTALL.md](INSTALL.md)。

完成后用简单话说明成品位置、双击后点句播放，以及下次提供新音频时可发送“用这个 Skill 做新的精听材料”。

## 材料与结果

处理用户提供的材料。公开演示或分发成品需要相应的音频与原文使用授权。本仓库不包含考试音频或原文。

不要承诺处理时间、不劈词准确率或提分效果。完成抽查仍可能有未覆盖问题，报告实际检查范围即可。
