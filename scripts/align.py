#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1) 把 whisper 的 word-level 时间戳按标点切成「句子」
2) 与官方真题原文做序列对齐，用官方原文校正 ASR 文本并标注说话人
3) 输出 sentences.json
"""
import json
import re
import sys
from difflib import SequenceMatcher

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402
import common  # noqa: E402

# ---------------- 1. 读参考原文，拆句 ----------------
# 常见真题/教材的板块标题行。若你的原文用别的标题，加进这个正则即可。
SECTION_RE = re.compile(
    r"^(Long Conversation \d+|Conversation \d+|Passage \d+(?: \(Recording \d+\))?"
    r"|Recording (?:One|Two|Three|\d+)|News Report \d+|Lecture \d+"
    r"|Section [A-Z0-9]+|Part [A-Z0-9]+|Questions? \d+[-–]\d+)\s*$",
    re.I,
)
Q_RE = re.compile(r"^Q\d+\.")
SPEAKER_RE = re.compile(r"^([MW]):\s*")


Q_NUM_RE = re.compile(r"^Q\d+\.")


def load_reference(path):
    """返回 [(section, speaker, sentence)]"""
    out = []
    section = "Directions"
    speaker = None
    buf = ""

    def flush(sec, spk):
        nonlocal buf
        text = buf.strip()
        buf = ""
        if not text:
            return
        if spk == "Q":
            # 按题号切，保证 "Q1. xxx?" 是一条
            parts = re.split(r"\s+(?=Q\d+\.)", text)
        else:
            # 允许引号结尾（如 testing." In）也能断句
            parts = re.split(r"(?<=[.!?])[\"']?\s+(?=[\"'\u4e00-\u9fffA-Z0-9])", text)
        for p in parts:
            p = p.strip()
            if p:
                out.append((sec, spk, p))

    with open(path, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f]

    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln:
            i += 1
            continue
        m = SECTION_RE.match(ln)
        if m:
            flush(section, speaker)
            section = m.group(1)
            speaker = None
            i += 1
            continue
        if Q_NUM_RE.match(ln):
            flush(section, speaker)
            qtext = ln
            j = i + 1
            while j < len(lines) and lines[j] \
                    and not Q_NUM_RE.match(lines[j]) \
                    and not SECTION_RE.match(lines[j]) \
                    and not SPEAKER_RE.match(lines[j]):
                qtext += " " + lines[j]
                j += 1
            buf = qtext
            flush(section, "Q")
            i = j
            continue
        sm = SPEAKER_RE.match(ln)
        if sm:
            flush(section, speaker)
            speaker = "Man" if sm.group(1) == "M" else "Woman"
            buf = ln[sm.end():].strip()
            i += 1
            continue
        buf = (buf + " " + ln).strip()
        i += 1
    flush(section, speaker)
    return out


# ---------------- 2. 从 whisper words 切句 ----------------
CJK = r"\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"


def clean_text(t):
    """清理中文被 whisper 拆出的多余空格，并统一排版"""
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(f"([{CJK}]) +([{CJK}])", r"\1\2", t)
    t = re.sub(f" +([{CJK}])", r"\1", t)
    t = re.sub(f"([{CJK}]) +", r"\1", t)
    return t.strip()


def build_sentences(segments):
    """把带 word 时间戳的 segments 按中英文句末标点合并成句子"""
    sents = []
    cur = {"words": [], "text": ""}

    def emit():
        if not cur["words"]:
            return
        sents.append({
            "start": cur["words"][0]["s"],
            "end": cur["words"][-1]["e"],
            # 词级锚点：切分时用它们夹住搜索窗口，保证不把任何一个词劈成两半
            "w_start": cur["words"][0]["s"],
            "w_end": cur["words"][-1]["e"],
            "last_w_start": cur["words"][-1]["s"],
            "text": clean_text(cur["text"]),
        })

    for seg in segments:
        words = seg.get("words") or []
        if not words:
            emit2 = {"start": seg["start"], "end": seg["end"],
                     "w_start": seg["start"], "w_end": seg["end"],
                     "last_w_start": seg["start"] - 0.30,
                     "text": clean_text(seg["text"])}
            sents.append(emit2)
            continue
        for w in words:
            cur["words"].append(w)
            cur["text"] = (cur["text"] + " " + w["w"]).strip()
            # 句末判定：中英文句末标点；至少 2 个词（中文按词块）或 3 个英文词
            if re.search(r"[.!?。！？]$", w["w"]) and (
                len(cur["words"]) >= 2 or len(re.sub(f"[{CJK}]", " ", cur["text"]).split()) >= 3
            ):
                emit()
                cur = {"words": [], "text": ""}
    emit()
    return [s for s in sents if s["text"]]


def norm(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sim(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


# ---------------- 3. 序列对齐（DP，保序） ----------------
def align(asr, ref, gap_open=-0.25, gap_ext=-0.05):
    """返回 list of (asr_idx or None, ref_idx or None)"""
    n, m = len(asr), len(ref)
    NEG = -1e9
    # M[i][j] 最优得分；指针用简化实现：只存得分与回溯
    M = [[NEG] * (m + 1) for _ in range(n + 1)]
    P = [[0] * (m + 1) for _ in range(n + 1)]  # 0 diag, 1 up(asr gap), 2 left(ref gap)
    M[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            best, ptr = NEG, 0
            if i > 0 and j > 0:
                s = sim(asr[i - 1]["text"], ref[j - 1][2]) * 2 - 1  # 映射到 [-1,1]
                v = M[i - 1][j - 1] + s
                if v > best:
                    best, ptr = v, 0
            if i > 0:
                v = M[i - 1][j] + (gap_ext if P[i - 1][j] == 1 else gap_open)
                if v > best:
                    best, ptr = v, 1
            if j > 0:
                v = M[i][j - 1] + (gap_ext if P[i][j - 1] == 2 else gap_open)
                if v > best:
                    best, ptr = v, 2
            M[i][j] = best
            P[i][j] = ptr
    res = []
    i, j = n, m
    while i > 0 or j > 0:
        p = P[i][j]
        if p == 0:
            res.append((i - 1, j - 1)); i -= 1; j -= 1
        elif p == 1:
            res.append((i - 1, None)); i -= 1
        else:
            res.append((None, j - 1)); j -= 1
    res.reverse()
    return res


# 考试说明 / 试音等「非正文」句子，归入 Directions 板块
DIRECTION_HINTS = [
    "end of listening comprehension", "试音", "全国大学英语六级考试",
    "全国大学英语四级考试", "directions for", "in this section, you will",
    "at the end of", "now let's begin",
]


def main():
    a = common.get_args("把 ASR 结果与官方原文对齐，输出 sentences.json", need_audio=False)
    with open(common.P(a.work, "segments_raw.json"), encoding="utf-8") as f:
        raw = json.load(f)
    asr_sents = build_sentences(raw["segments"])
    if a.ref and os.path.exists(a.ref):
        ref_sents = load_reference(a.ref)
    else:
        ref_sents = []
        print("未提供官方原文（--ref），进入纯 ASR 模式", file=sys.stderr)
    print(f"ASR 句子 {len(asr_sents)} 条 / 参考原文句子 {len(ref_sents)} 条", file=sys.stderr)

    pairs = align(asr_sents, ref_sents) if ref_sents else \
        [(i, None) for i in range(len(asr_sents))]

    out = []
    for ai, rj in pairs:
        if ai is None:
            continue  # 原文里有但音频未识别到 -> 跳过（无时间戳无法切）
        s = asr_sents[ai]
        item = {
            "start": s["start"], "end": s["end"],
            # 词级锚点（切分时用来夹住搜索窗口，保证不把词劈成两半）
            "w_start": s.get("w_start", s["start"]),
            "w_end": s.get("w_end", s["end"]),
            "last_w_start": s.get("last_w_start", s["start"]),
            "asr": s["text"],
        }
        if rj is not None:
            sec, spk, text = ref_sents[rj]
            sc = sim(s["text"], text)
            item.update({"section": sec, "speaker": spk, "ref": text, "score": round(sc, 3)})
            item["text"] = text if sc >= 0.55 else s["text"]
            item["src"] = "official" if sc >= 0.55 else "asr"
        else:
            item.update({"section": None, "speaker": None, "ref": None, "score": 0.0,
                         "text": s["text"], "src": "asr"})
        out.append(item)

    # 板块归属：未匹配到原文的句子沿用前一句所属板块
    last_sec = None
    for x in out:
        if x.get("section"):
            last_sec = x["section"]
        else:
            x["section"] = last_sec
    for x in out:
        t = (x["text"] or "").lower()
        if not x["section"] or any(h in t for h in DIRECTION_HINTS):
            x["section"] = "Directions"
            x["speaker"] = None

    with open(common.P(a.work, "sentences.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": raw["duration"], "sentences": out}, f, ensure_ascii=False, indent=1)

    matched = sum(1 for x in out if x["src"] == "official")
    print(f"输出 {len(out)} 句，其中 {matched} 句与官方原文匹配成功", file=sys.stderr)


if __name__ == "__main__":
    main()
