#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端校验：把切出来的每个片段单独重新识别一遍，
检查片段音频的内容是否就是它标注的那一句（不多、不少）。
  - 尾巴多出下一句开头的词  -> 「尾巴留半截音，下一句又重复」
  - 标注句尾的词在音频里找不到 -> 尾音被切掉
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402
import common  # noqa: E402  导入即打上 av 兼容补丁

from faster_whisper import WhisperModel  # noqa: E402

WORD = re.compile(r"[a-z']+")


def norm(t):
    return WORD.findall(t.lower())


def main():
    args = common.get_args("校验切出的片段是否恰好是标注的那一句", need_audio=False)
    OUTDIR = common.P(args.work, "audio_sentences")
    sents = common.load_sentences(args.work)["sentences"]

    ids = os.environ.get("VERIFY_IDS", "")
    pick = sorted({int(x) for x in ids.split(",") if x.strip()}) if ids else list(range(1, len(sents) + 1))
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=8)
    results = [None] * len(sents)
    for n, i in enumerate(pick, 1):
        p = f"{OUTDIR}/{i:03d}.mp3"
        if not os.path.exists(p):
            continue
        segs, _ = model.transcribe(p, language=args.lang, beam_size=5,
                                   vad_filter=False, condition_on_previous_text=False)
        txt = " ".join(x.text for x in segs).strip()
        results[i - 1] = txt
        if n % 10 == 0:
            print(f"  识别 {n}/{len(pick)}", flush=True)

    with open(common.P(args.work, "verify_asr.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)

    over, under = [], []
    for i, s in enumerate(sents):
        heard = norm(results[i] or "")
        mine = norm(s["text"])
        nxt = norm(sents[i + 1]["text"]) if i + 1 < len(sents) else []
        if not heard or not mine:
            continue
        # 尾巴溢出：听到的末尾 2 个词 出现在下一句开头 3 个词里
        if nxt and len(heard) >= 2 and heard[-1] in nxt[:3] and heard[-1] != mine[-1]:
            over.append((i + 1, heard[-3:], mine[-2:], nxt[:3]))
        # 尾巴缺失：我标注的最后 1 个词，在听到的里找不到
        elif mine and mine[-1] not in heard:
            under.append((i + 1, mine[-3:], heard[-3:]))

    print(f"\n总片段 {len(sents)}")
    print(f"尾巴溢出到下一句（会听到下一句开头重复）: {len(over)}")
    for x in over[:15]:
        print("   ", x)
    print(f"尾巴被切掉（句尾词在音频里找不到）: {len(under)}")
    for x in under[:15]:
        print("   ", x)


if __name__ == "__main__":
    main()
