# -*- coding: utf-8 -*-
"""
共享工具：命令行参数解析 + 音频解码/编码 + RMS 能量计算。

所有脚本都从同一个工作目录读写，中间产物命名固定：
    segments_raw.json   whisper 原始转写（含词级时间戳）
    sentences.json      逐句时间轴（text / start / end / section / speaker ...）
    translations.json   {序号: 中文译文}
    audio_sentences/    001.mp3 002.mp3 ...
    config.json         记录源音频路径、标题等，后续步骤自动读取
"""
import argparse
import json
import os

# 有代理时直连 huggingface.co 常常 502，自动切到镜像，省得每次手动 export
if not os.environ.get("HF_ENDPOINT") and not os.environ.get("HF_HUB_OFFLINE"):
    if os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") \
            or os.environ.get("ALL_PROXY") or os.environ.get("https_proxy"):
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print("[env] 检测到代理，模型源已自动切换到 https://hf-mirror.com", flush=True)

import av
import numpy as np

# av>=14 移除了 metadata_errors 参数，而 faster-whisper 1.2.x 仍在传，做兼容补丁
_orig_open = av.open


def _open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_open(*args, **kwargs)


av.open = _open


def get_args(desc="", need_audio=True):
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--work", default=os.environ.get("LSI_WORK", "."),
                   help="工作目录（中间产物与最终 HTML 都放这里）")
    p.add_argument("--audio", default=os.environ.get("LSI_AUDIO"),
                   help="源音频文件（mp3/m4a/wav/flac 等）")
    p.add_argument("--ref", default=None,
                   help="官方原文/标准转写 txt（可选，用于校正 ASR 文本与切分板块）")
    p.add_argument("--title", default=None, help="页面标题")
    p.add_argument("--model", default=None,
                   help="whisper 模型名，默认 large-v3-turbo（快且够准）；"
                        "想要极致准确率用 large-v3，慢机器用 small / medium")
    p.add_argument("--lang", default="en", help="音频语言代码，默认 en")
    p.add_argument("--out", default=None, help="输出文件名（覆盖默认）")
    p.add_argument("--restart", action="store_true",
                   help="忽略已有产物/进度，从头重做")
    p.add_argument("--limit", type=int, default=None,
                   help="本次最多处理多少块/句（分批推进，可反复执行直到做完）")
    p.add_argument("--no-batch", action="store_true",
                   help="关闭批量推理（默认开启批处理，速度更快）")
    p.add_argument("--batch-size", type=int, default=8,
                   help="批量推理的批大小，默认 8；内存紧张可调小到 2~4")
    p.add_argument("--jobs", type=int, default=2,
                   help="并行跑几个转写进程，默认 2；核多可加到 3~4，内存小就设 1")
    a = p.parse_args()
    a.work = os.path.abspath(os.path.expanduser(a.work))
    os.makedirs(a.work, exist_ok=True)
    a.restart = bool(getattr(a, "restart", False)) or bool(os.environ.get("LSI_RESTART"))
    # 记住上下文，后续步骤不必重复传参
    cfg_path = os.path.join(a.work, "config.json")
    cfg = {}
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    for k in ("audio", "ref", "title", "model", "lang"):
        v = getattr(a, k, None)
        if v:
            cfg[k] = v
    a.audio = os.path.abspath(os.path.expanduser(cfg["audio"])) if cfg.get("audio") else None
    if need_audio and not a.audio:
        p.error("需要 --audio 指定源音频（或先跑 transcribe.py 写入 config.json）")
    if not getattr(a, "title", None):
        a.title = cfg.get("title") or "逐句精听索引"
    if not getattr(a, "model", None):
        a.model = cfg.get("model") or "large-v3-turbo"   # 默认用 turbo，比 large-v3 快数倍
    a.ref = os.path.abspath(os.path.expanduser(cfg["ref"])) if cfg.get("ref") else None
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    return a


def P(work, name):
    return os.path.join(work, name)


def load_sentences(work):
    with open(P(work, "sentences.json"), encoding="utf-8") as f:
        return json.load(f)


def save_sentences(work, d):
    with open(P(work, "sentences.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def load_all(src):
    """解码整段音频 -> int16 ndarray (channels, samples), 采样率, 声道布局"""
    container = av.open(src)
    stream = container.streams.audio[0]
    sr = stream.rate
    layout = stream.layout.name if stream.layout else "stereo"
    chunks = []
    for frame in container.decode(stream):
        chunks.append(frame.to_ndarray())
    data = np.concatenate(chunks, axis=1)
    container.close()
    data = np.clip(data * 32767.0, -32768, 32767).astype(np.int16)
    return data, sr, layout


def compute_rms(mono, sr, win=0.010, k=5):
    """逐窗 RMS 能量曲线，win=10ms"""
    w = max(1, int(sr * win))
    n = len(mono) // w
    rms = np.sqrt((mono[:n * w].reshape(n, w) ** 2).mean(axis=1))
    rms = np.convolve(rms, np.ones(k) / k, mode="same")
    return rms, win


def encode_clip(data, sr, layout, start, end, path, bitrate=128000):
    """按时间区间切片并编码为 mp3"""
    i0 = max(0, int(start * sr))
    i1 = min(data.shape[1], int(end * sr))
    if i1 <= i0:
        return False
    seg = data[:, i0:i1]
    out = av.open(path, "w")
    ost = out.add_stream("libmp3lame", rate=sr)
    ost.layout = layout
    ost.bit_rate = bitrate
    fs = 1152
    n = seg.shape[1]
    for k in range(0, n, fs):
        block = seg[:, k:k + fs]
        if block.shape[1] < fs:
            block = np.pad(block, ((0, 0), (0, fs - block.shape[1])), mode="constant")
        frame = av.AudioFrame.from_ndarray(block, format="s16p", layout=layout)
        frame.sample_rate = sr
        frame.time_base = ost.time_base
        for packet in ost.encode(frame):
            out.mux(packet)
    for packet in ost.encode():
        out.mux(packet)
    out.close()
    return True


def encode_mono(seg, sr, bitrate=48000):
    """seg: int16 ndarray (1, n) -> mp3 bytes（单声道，用于内嵌单文件版）"""
    import io
    buf = io.BytesIO()
    out = av.open(buf, "w", format="mp3")
    ost = out.add_stream("libmp3lame", rate=sr)
    ost.layout = "mono"
    ost.bit_rate = bitrate
    fs = 1152
    n = seg.shape[1]
    for k in range(0, n, fs):
        block = seg[:, k:k + fs]
        if block.shape[1] < fs:
            block = np.pad(block, ((0, 0), (0, fs - block.shape[1])), mode="constant")
        frame = av.AudioFrame.from_ndarray(block, format="s16p", layout="mono")
        frame.sample_rate = sr
        frame.time_base = ost.time_base
        for packet in ost.encode(frame):
            out.mux(packet)
    for packet in ost.encode():
        out.mux(packet)
    out.close()
    return buf.getvalue()


def mmss(t):
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def slug(s):
    """把标题里的非法文件名字符换掉"""
    bad = '/\\:*?"<>|'
    for c in bad:
        s = s.replace(c, "_")
    return s.strip() or "index"
