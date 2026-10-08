# 环境配置与常见问题

本文件供制作材料的智能体阅读。先检查用户工作环境，再安装依赖；运行目录与音频输出目录应独立于 Skill 目录。

## Python 与依赖

使用 Python 3.10+。依赖为 `faster-whisper`、`av`（PyAV）、`numpy`，见 `requirements.txt`。流水线使用 PyAV 编解码，不调用外部 ffmpeg 命令。

```bash
python scripts/prepare.py --install
```

若系统 Python 受保护，在工作目录建立虚拟环境，使用其中的 Python 运行全部步骤。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Windows 使用虚拟环境 Scripts 目录下的 python.exe。不要将不同 Python 的 pip 与运行命令混用。

## 模型下载与网络

首次转写需下载模型。常见模型缓存位置为 `~/.cache/huggingface/`，已缓存时可复用。镜像、代理与访问条件由用户环境决定；遇到下载失败先检查实际错误，再选择可用源。可通过 `HF_ENDPOINT` 指定模型源，`PIP_INDEX_URL` 指定包源。

`common.py` 包含镜像与 PyAV 的兼容处理。仍遇到模型仓库不存在、代理错误或网络超时，应检查模型名、当前源及网络。

## 常见报错

| 现象 | 检查与处理 |
|---|---|
| `av.open` 不支持 `metadata_errors` | 脚本通过 `common.py` 做兼容处理；确认用的是完整包和同一运行环境 |
| PyAV 编码失败或 `libmp3lame` 不可用 | 检查安装的 PyAV 及编码器；必要时重装支持所需编码器的版本 |
| 转写慢 | 模型、硬件、并行度与音频长度影响耗时；先用短材料跑通，按脚本帮助选择模型 |
| 出现不属于录音的文字 | 检查静音、VAD 和自动识别结果；结合原文、补漏结果与抽听核验 |
| 重新转写后页面仍是旧内容 | 上游变化会影响对齐、补漏、切分和页面；重新生成所有受影响的下游产物，避免续跑跳过旧步骤 |
| 中文为空 | 脚本不自动翻译；由智能体生成与最终句子编号对应的译文，再生成页面 |

不要承诺固定耗时。更换模型或调整转写后，需要重新检查下游时间轴和片段；不能仅重跑转写而沿用所有旧产物。
