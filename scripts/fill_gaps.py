#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
找出「有声音但语音识别没覆盖到」的区间（如被漏掉的题目朗读），
单独补识别后插回句子列表，避免它们被并进相邻句子、拖长片段。
"""
import json
import os
import re

import numpy as np
import av
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402
import common  # noqa: E402

from faster_whisper import WhisperModel  # noqa: E402


def voice_regions(mono, sr, thresh=0.008, min_dur=0.8, pad=0.15):
    """返回 [(start, end)]，单位为秒"""
    w = int(sr * 0.02)
    n = len(mono) // w
    rms = np.sqrt((mono[:n * w].reshape(n, w) ** 2).mean(axis=1))
    hot = rms > thresh
    # 膨胀，把零星的低能量帧也并进来
    k = int(0.25 / 0.02)
    hot = np.convolve(hot.astype(float), np.ones(k), mode="same") > 0.5
    regions = []
    i = 0
    while i < n:
        if hot[i]:
            j = i
            while j < n and hot[j]:
                j += 1
            st = max(0.0, i * 0.02 - pad)
            en = min(len(mono) / sr, j * 0.02 + pad)
            if en - st >= min_dur:
                regions.append((st, en))
            i = j
        else:
            i += 1
    return regions


def uncovered(regions, sents, min_len=1.2):
    """语音区间中，没有被任何已识别句子覆盖到的部分"""
    out = []
    for a, b in regions:
        cur = a
        for s in sents:
            ss, se = s["start"], s["end"]
            if se <= cur or ss >= b:
                continue
            if ss - cur >= min_len:
                out.append((cur, min(ss, b)))
            cur = max(cur, se)
            if cur >= b:
                break
        if b - cur >= min_len:
            out.append((cur, b))
    return out


def write_wav(data, sr, start, end, path):
    i0 = max(0, int(start * sr))
    i1 = min(data.shape[1], int(end * sr))
    seg = data[:, i0:i1]
    out = av.open(path, "w")
    st = out.add_stream("pcm_s16le", rate=sr)
    st.layout = "stereo"
    fs = 1024
    n = seg.shape[1]
    for k in range(0, n, fs):
        block = seg[:, k:k + fs]
        frame = av.AudioFrame.from_ndarray(block, format="s16p", layout="stereo")
        frame.sample_rate = sr
        frame.time_base = st.time_base
        for p in st.encode(frame):
            out.mux(p)
    for p in st.encode():
        out.mux(p)
    out.close()


def main():
    args = common.get_args("补识别「有声音但没被转写覆盖」的段落")
    TMP = common.P(args.work, "_tmp")
    d = common.load_sentences(args.work)
    sents = d["sentences"]

    print("解码音频 ...", flush=True)
    data, sr, _layout = common.load_all(args.audio)
    mono = data.mean(axis=0).astype(np.float32) / 32768.0
    regions = voice_regions(mono, sr)
    gaps = uncovered(regions, sents)
    print(f"语音区间 {len(regions)} 段，其中未被识别覆盖的 {len(gaps)} 段", flush=True)
    for a, b in gaps:
        print(f"    {a:8.2f} - {b:8.2f}  ({b-a:.1f}s)", flush=True)
    if not gaps:
        print("无需补识别")
        return

    os.makedirs(TMP, exist_ok=True)
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=8)

    added = []
    for i, (a, b) in enumerate(gaps):
        wav = f"{TMP}/gap{i:03d}.wav"
        write_wav(data, sr, a, b, wav)
        segs, _ = model.transcribe(
            wav, language=args.lang, beam_size=5, vad_filter=True,
            condition_on_previous_text=False, word_timestamps=True,
            initial_prompt="A short spoken sentence from a listening comprehension test.",
        )
        for seg in segs:
            t = seg.text.strip()
            if not t or "..." in t or "…" in t:
                continue  # 过滤模型照抄提示词产生的幻觉文本
            wl = getattr(seg, "words", None) or []
            ws = wl[0].start if wl else seg.start
            we = wl[-1].end if wl else seg.end
            lws = wl[-1].start if wl else seg.start
            added.append({
                "start": round(a + seg.start, 3),
                "end": round(a + seg.end, 3),
                "w_start": round(a + ws, 3),
                "w_end": round(a + we, 3),
                "last_w_start": round(a + lws, 3),
                "asr": t,
                "section": None,
                "speaker": "Q" if re.search(r"question|^\s*Q\d", t, re.I) else None,
                "ref": None, "score": 0.0,
                "text": t, "src": "asr",
            })
            print(f"    + {a + seg.start:8.2f} {t[:80]}", flush=True)

    if added:
        sents.extend(added)
        sents.sort(key=lambda x: (x["start"], x["end"]))
        # 板块归属沿用前一句
        last_sec = None
        for x in sents:
            if x.get("section"):
                last_sec = x["section"]
            else:
                x["section"] = last_sec
        for x in sents:
            if not x["section"]:
                x["section"] = "Transcript"
        common.save_sentences(args.work, d)
        print(f"补入 {len(added)} 句，现共 {len(sents)} 句")


if __name__ == "__main__":
    main()
