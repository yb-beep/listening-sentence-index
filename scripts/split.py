#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按句子边界切分音频，每句输出一个 mp3（用 PyAV，无需外部 ffmpeg）"""
import json
import os
import sys

import av
import numpy as np

import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402
import common  # noqa: E402


def encode_clip(data, sr, layout, start, end, path):
    i0 = max(0, int(start * sr))
    i1 = min(data.shape[1], int(end * sr))
    if i1 <= i0:
        return False
    seg = data[:, i0:i1]
    out = av.open(path, "w")
    ost = out.add_stream("libmp3lame", rate=sr)
    ost.layout = layout
    ost.bit_rate = 128000
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


def compute_rms(mono, sr, win=0.010, k=5):
    return common.compute_rms(mono, sr, win, k)


def tighten(sents, rms, win, thresh=0.006, max_gap=2.5):
    """
    识别给的句子结束时间有时会漂到很远（把后面的题目、留白一起圈进来）。
    这里把每句的 end 收紧到「从本句开头起、连续语音的最后一点」，
    中间出现超过 max_gap 秒静音就认为本句已结束。
    """
    for s in sents:
        i0 = max(0, int(s["start"] / win))
        i1 = min(len(rms), int(s["end"] / win))
        if i1 - i0 < 1:
            continue
        idx = np.nonzero(rms[i0:i1] > thresh)[0]
        if len(idx) == 0:
            continue
        end = (i0 + int(idx[0]) + 1) * win
        last = int(idx[0])
        for k in idx:
            if (int(k) - last) * win > max_gap:
                break
            end = (i0 + int(k) + 1) * win
            last = int(k)
        if end < s["end"]:
            s["end"] = round(end, 3)


def build_bounds(sents, total, rms, win, peak):
    """
    为每个句子边界找「静音谷」，且边界只允许落在词级窗口内。

    关键约束（这是不再把单词劈成两半的原因）：
      边界 i 必须落在 [句i 最后一个词的起点, 句i+1 第一个词的起点] 之间。
      - 下界保证句 i 至少完整发出它的最后一个词（不会只剩半截音）
      - 上界保证句 i+1 的第一个词没被上一句吃掉（下一句不会重复念）
    在这个窗口里再取最长静音段的中点；窗口内无静音时退化为能量最低点。
    """
    n = len(rms)
    # 自适应静音阈值：底噪的若干倍，明显低于语音中位能量
    thr = max(0.0015, float(np.percentile(rms, 50)) * 0.10)

    def idx(t):
        return max(0, min(n - 1, int(t / win)))

    def silent_runs(a, b):
        """[a,b] 内所有静音段，返回 [(起点秒, 终点秒)]"""
        i0 = max(0, int(a / win))
        i1 = min(n, int(b / win))
        if i1 - i0 < 1:
            return []
        cold = rms[i0:i1] < thr
        runs, i = [], 0
        while i < len(cold):
            if cold[i]:
                j = i
                while j < len(cold) and cold[j]:
                    j += 1
                runs.append(((i0 + i) * win, (i0 + j) * win))
                i = j
            else:
                i += 1
        return runs

    def last_silent(a, b, min_len=0.06):
        """
        取窗口内【最后】一段够长的静音的中点。
        句间停顿一定是窗口内最后一段静音 —— 用它而不是「最长静音」，
        可以避免误选句内逗号处的停顿。
        """
        runs = [r for r in silent_runs(a, b) if r[1] - r[0] >= min_len]
        if not runs:
            return None
        s, e = runs[-1]
        return (s + e) / 2, e - s

    def quietest(a, b):
        """窗口内没有静音时退而求其次：取能量最低点，并轻微偏好靠后（靠近下一句词头）"""
        i0, i1 = idx(a), idx(b)
        if i1 <= i0:
            return max(0.0, a)
        seg = rms[i0:i1 + 1]
        pos = (np.arange(i0, i1 + 1) + 0.5) * win
        score = seg / peak + 0.05 * (np.abs(pos - b) / max(b - a, 1e-6))
        return float((i0 + int(np.argmin(score)) + 0.5) * win)

    def window(i):
        """
        返回边界 i（句 i 与句 i+1 之间）的合法搜索窗口 (lo, hi)。
        实测 whisper 的词时间戳整体偏早 200~350ms，所以上界要给 +0.40 的余量，
        否则真正的句间静音会被排除在窗口之外，边界只能落在尾音上（词被劈开）。
        """
        a = sents[i]
        b = sents[i + 1]
        lo = a.get("last_w_start", a["end"] - 0.40)      # 句 i 最后一个词起
        hi = b.get("w_start", b["start"]) + 0.40         # 句 i+1 第一个词起 + 补偿
        if hi <= lo:                                     # 时间戳异常时兜底
            hi = lo + 0.40
        lo = max(lo, hi - 2.5)                           # 最多往前找 2.5s，避免跳到句内
        return max(0.0, lo - 0.05), hi

    bounds = [quietest(max(0.0, sents[0].get("w_start", sents[0]["start"]) - 0.45),
                       max(0.05, sents[0].get("w_start", sents[0]["start"]) - 0.02))]
    levels = []
    silent_hits = 0
    for i in range(len(sents) - 1):
        lo, hi = window(i)
        r = last_silent(lo, hi)
        if r:
            bounds.append(r[0])
            silent_hits += 1
        else:
            bounds.append(quietest(lo, hi))
        levels.append(float(rms[idx(bounds[-1])]))
    last_end = sents[-1].get("w_end", sents[-1]["end"])
    bounds.append(quietest(min(total, last_end + 0.05), min(total, last_end + 0.50)))

    # 单调化：保证每个片段至少 50ms
    for i in range(1, len(bounds)):
        if bounds[i] <= bounds[i - 1] + 0.05:
            bounds[i] = bounds[i - 1] + 0.05
    bounds[-1] = min(bounds[-1], total)
    print(f"  静音阈值 {thr:.4f} · 落在真实静音段的边界 {silent_hits}/{len(levels)}", flush=True)
    return bounds, levels


def trim_silence(start, end, rms, win, peak, thresh=0.006, pad_in=0.12, pad_out=0.20):
    """裁掉片段首尾过长的静音，让点开就出声、说完就收尾（不改变句子本身）"""
    n = len(rms)
    i0 = max(0, int(start / win))
    i1 = min(n, int(end / win))
    if i1 - i0 < 2:
        return start, end
    idx = np.nonzero(rms[i0:i1] > thresh)[0]
    if len(idx) == 0:
        return start, end
    a = i0 + int(idx[0])
    b = i0 + int(idx[-1]) + 1
    return max(start, a * win - pad_in), min(end, b * win + pad_out)


def main():
    args = common.get_args("按句子边界切分音频，每句一个 mp3")
    OUTDIR = common.P(args.work, "audio_sentences")
    os.makedirs(OUTDIR, exist_ok=True)
    d = common.load_sentences(args.work)
    sents = d["sentences"]
    total = d["duration"]
    if not sents:
        raise ValueError("句子时间轴为空，请先检查转写与对齐结果")

    print("解码源音频 ...", flush=True)
    data, sr, layout = common.load_all(args.audio)
    print(f"  {data.shape[1]/sr:.1f}s @ {sr}Hz {layout}", flush=True)

    mono = data.mean(axis=0).astype(np.float32) / 32768.0
    rms, win = compute_rms(mono, sr)
    peak = float(rms.max()) or 1.0
    THR = max(0.0015, float(np.percentile(rms, 50)) * 0.10)
    tighten(sents, rms, win, thresh=THR)
    bounds, levels = build_bounds(sents, total, rms, win, peak)
    rms_for_trim = rms
    loud = sum(1 for x in levels if x > THR * 6)
    print(f"  边界 {len(bounds)} 个，落在明显有声处的 {loud} 个（{loud/max(1,len(levels)):.0%}）", flush=True)

    # 续传：已有 mp3 且不要求重切时直接跳过，重跑只补缺失的那几句
    restart = args.restart
    ok = 0
    skipped = 0
    for i, s in enumerate(sents, 1):
        start, end = trim_silence(bounds[i - 1], bounds[i], rms_for_trim, win, peak, thresh=THR)
        path = f"{OUTDIR}/{i:03d}.mp3"
        if (not restart and os.path.exists(path) and os.path.getsize(path) > 0
                and os.path.getmtime(path) >= max(os.path.getmtime(args.audio),
                                                  os.path.getmtime(__file__),
                                                  os.path.getmtime(common.__file__))
                and s.get("clip_start") == round(start, 3)
                and s.get("clip_end") == round(end, 3)):
            s["file"] = f"{i:03d}.mp3"
            skipped += 1
            if i % 50 == 0:
                print(f"  {i}/{len(sents)}", flush=True)
            continue
        if encode_clip(data, sr, layout, start, end, path):
            s["file"] = f"{i:03d}.mp3"
            s["clip_start"] = round(start, 3)
            s["clip_end"] = round(end, 3)
            ok += 1
        else:
            raise ValueError(f"第 {i} 句的音频区间无效：{start:.3f}–{end:.3f}s")
        if i % 50 == 0:
            print(f"  {i}/{len(sents)}", flush=True)

    if skipped:
        print(f"  其中 {skipped} 句已存在，直接沿用（想全部重切加 --restart）", flush=True)
    if not ok and not skipped:
        print("  没有切出任何片段：请确认 audio_sentences 目录可写", flush=True)
    common.save_sentences(args.work, d)
    print(f"DONE 切出 {ok} 个片段 -> {OUTDIR}")


if __name__ == "__main__":
    main()
