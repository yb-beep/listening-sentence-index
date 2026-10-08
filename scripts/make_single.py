#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「单文件自包含」版逐句精听索引：
- 所有句子音频以 base64 内嵌，不依赖服务器、不依赖同目录文件，双击即播
- 精听模式：英文原文 + 中文译文默认隐藏，可全局切换，也可单句揭开
"""
import base64
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402
import common  # noqa: E402

from page_tpl import HEAD, TAIL, DICT_BAR  # noqa: E402

BITRATE = 48000  # 单声道 48kbps，语音足够清晰

# 板块名 -> 中文显示名；工作目录里的 sections.json 可覆盖/补充
DEFAULT_SECTION_CN = {
    "Directions": "考试说明",
    "Transcript": "正文",
    "Long Conversation 01": "长对话 1",
    "Long Conversation 02": "长对话 2",
    "Passage 01": "短文 1",
    "Passage 02": "短文 2",
    "Passage 03 (Recording 01)": "讲话/讲座 1",
    "Recording One": "讲话/讲座 1",
    "Recording 02": "讲话/讲座 2",
    "Recording Two": "讲话/讲座 2",
    "Recording 03": "讲话/讲座 3",
    "Recording Three": "讲话/讲座 3",
}


mmss = common.mmss
esc = common.esc


def encode_mono(seg, sr):
    return common.encode_mono(seg, sr, bitrate=BITRATE)


def speaker_of(s):
    sec = s.get("section") or ""
    spk = s.get("speaker")
    if sec == "Directions":
        return "提示"
    if spk in ("Man", "Woman"):
        return "男" if spk == "Man" else "女"
    if spk == "Q":
        return "题目"
    if sec.startswith("Long Conversation"):
        return "对话"
    return "独白"


def main():
    args = common.get_args("生成单文件自包含版精听索引（音频 base64 内嵌）")
    SECTION_CN = dict(DEFAULT_SECTION_CN)
    custom = common.P(args.work, "sections.json")
    if os.path.exists(custom):
        try:
            with open(custom, encoding="utf-8") as f:
                SECTION_CN.update(json.load(f))
        except Exception as e:
            print(f"sections.json 读取失败，忽略：{e}", file=sys.stderr)

    d = common.load_sentences(args.work)
    sents = d["sentences"]
    if not sents:
        raise ValueError("句子时间轴为空，无法生成精听网页")

    # 续传：成品比所有输入都新时没必要重做（要强制重生成加 --restart）
    OUT = common.P(args.work, args.out or f"{common.slug(args.title)}（单文件版）.html")
    if not args.restart and os.path.exists(OUT):
        deps = [common.P(args.work, "sentences.json"), common.P(args.work, "translations.json"),
                common.P(args.work, "sections.json"), args.audio, __file__,
                common.P(os.path.dirname(__file__), "page_tpl.py"), common.__file__]
        deps = [p for p in deps if os.path.exists(p)]
        if deps and all(os.path.getmtime(OUT) >= os.path.getmtime(p) for p in deps):
            print(f"{os.path.basename(OUT)} 已是最新，跳过"
                  f"（想强制重生成加 --restart）。句数 {len(sents)}，"
                  f"{os.path.getsize(OUT)/1024/1024:.1f}MB")
            return
    try:
        with open(common.P(args.work, "translations.json"), encoding="utf-8") as f:
            tr = {int(k): v for k, v in json.load(f).items()}
    except FileNotFoundError:
        tr = {}

    print("解码源音频 ...", flush=True)
    data, sr, _layout = common.load_all(args.audio)
    mono = data.mean(axis=0).astype(np.int16)[None, :]
    print(f"  {data.shape[1]/sr:.1f}s @ {sr}Hz", flush=True)

    official = sum(1 for x in sents if x.get("src") == "official")
    n_tr = sum(1 for i in range(1, len(sents) + 1) if tr.get(i))
    parts = [f"共 {len(sents)} 句", f"原音频总长 {mmss(d['duration'])}"]
    if official:
        parts.append(f"{official} 句已与提供的原文自动对齐")
    if n_tr:
        parts.append(f"{n_tr} 句配有中文译文")
    parts.append("音频全部内嵌，单文件可独立播放")
    meta = " · ".join(parts)

    clips = []
    rows = []
    nav = []
    cur_sec = None
    sec_start = 1
    for i, s in enumerate(sents, 1):
        sec = s.get("section") or "Directions"
        if sec != cur_sec:
            cur_sec = sec
            anchor = f"g{len(nav)}"
            name = SECTION_CN.get(sec, sec)
            nav.append(f'<a href="#{anchor}">{esc(name)}</a>')
            if rows:
                rows.append("</tbody></table>")
                rows.append(f'<div class="secnav"><button class="secplay2" '
                            f'data-a="{sec_start}" data-b="{i-1}">▶ 连播本板块'
                            f'（{sec_start}–{i-1}）</button></div>')
                rows.append("</section>")
            sec_start = i
            rows.append(
                f'<section class="grp" id="{anchor}"><h2 data-sec="{esc(name)}">'
                f'<span class="lft"><button class="secplay" data-a="{i}" data-b="0" '
                f'title="连播本板块">&#9654;</button>{esc(name)}</span>'
                f'<span class="n">{esc(sec)}</span></h2><table><tbody>'
            )
        a, b = s["clip_start"], s["clip_end"]
        i0, i1 = int(a * sr), int(b * sr)
        clips.append(base64.b64encode(encode_mono(mono[:, i0:i1], sr)).decode())
        spk = speaker_of(s)
        cls = {"男": "m", "女": "w", "题目": "q", "提示": "x"}.get(spk, "x")
        cn = esc(tr.get(i, "") or "")
        cn_html = f'<div class="cn">{cn}</div>' if cn else ""
        rows.append(
            f'<tr class="row" data-i="{i-1}" data-t="{esc(s["text"])}">'
            f'<td class="idx">{i}</td>'
            f'<td class="tm"><button class="play" title="播放本句">&#9654;</button>'
            f'<span>{mmss(a)}</span></td>'
            f'<td class="spk"><span class="bd {cls}">{spk}</span></td>'
            f'<td class="tx"><button class="veil">显示原文</button>'
            f'<div><div class="en">{esc(s["text"])}</div>{cn_html}</div>'
            f'<button class="st" title="星标难句">&#9734;</button>'
            f'<button class="pin" title="重新遮住">&#128274;</button></td></tr>'
        )
        if i % 40 == 0:
            print(f"  编码 {i}/{len(sents)}", flush=True)
    rows.append("</tbody></table>")
    rows.append(f'<div class="secnav"><button class="secplay2" data-a="{sec_start}" '
                f'data-b="{len(sents)}">▶ 连播本板块（{sec_start}–{len(sents)}）</button></div>')
    rows.append("</section>")

    print(f"  音频内嵌 {sum(len(c) for c in clips)/1024/1024:.1f}MB (base64)", flush=True)

    # localStorage 键：同一份材料稳定不变，不同材料互不串味
    store_key = common.storage_key(args.title, sents)

    html = HEAD.replace('<div class="sub2" id="meta"></div>',
                        f'<div class="sub2">{esc(meta)}</div>')
    html = html.replace('<div class="nav" id="nav"></div>',
                        '<div class="nav">' + "".join(nav) + "</div>")
    html += "\n".join(rows)
    html += DICT_BAR
    html += TAIL.replace("__CLIPS__", json.dumps(clips, ensure_ascii=False))
    html = html.replace("__TITLE__", esc(args.title))
    html = html.replace("__STORE_KEY__", store_key)

    OUT = common.P(args.work, args.out or f"{common.slug(args.title)}（单文件版）.html")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"DONE -> {OUT} ({os.path.getsize(OUT)/1024/1024:.1f}MB)")


if __name__ == "__main__":
    main()
