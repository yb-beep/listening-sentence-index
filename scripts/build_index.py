#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成句子索引：HTML（可点句播放）+ CSV + Markdown"""
import csv
import json
import os
import shutil

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402
import common  # noqa: E402

# 板块名 -> 中文显示名。没命中的会直接显示英文原名。
# 想自定义：在工作目录放 sections.json，内容 {"Passage 01": "短文 1", ...}
DEFAULT_SECTION_CN = {
    "Directions": "考试说明",
    "Transcript": "正文",
    "Long Conversation 01": "长对话 1",
    "Long Conversation 02": "长对话 2",
    "Passage 01": "短文 1",
    "Passage 02": "短文 2",
    "Passage 03 (Recording 01)": "讲座/讲话 1",
    "Recording One": "讲座/讲话 1",
    "Recording Two": "讲座/讲话 2",
    "Recording Three": "讲座/讲话 3",
    "Recording 01": "讲座/讲话 1",
    "Recording 02": "讲座/讲话 2",
    "Recording 03": "讲座/讲话 3",
}
SPEAKER_CN = {"Man": "男", "Woman": "女", "Q": "题目", None: "—"}


def speaker_of(s):
    spk = s.get("speaker")
    if spk:
        return SPEAKER_CN.get(spk, "—")
    return "提示" if s.get("section") == "Directions" else "独白"


def mmss(x):
    m, s = divmod(int(x), 60)
    return f"{m:02d}:{s:02d}"


def main():
    a = common.get_args("生成句子索引：HTML + CSV + Markdown（依赖同目录 audio_sentences/）",
                        need_audio=False)
    TITLE = a.title
    SECTION_CN = dict(DEFAULT_SECTION_CN)
    custom = common.P(a.work, "sections.json")
    if os.path.exists(custom):
        try:
            with open(custom, encoding="utf-8") as f:
                SECTION_CN.update(json.load(f))
        except Exception as e:
            print(f"sections.json 读取失败，忽略：{e}", file=sys.stderr)

    d = common.load_sentences(a.work)
    sents = d["sentences"]

    # 复制整段音频，便于页面整体播放
    full_name = "full" + (os.path.splitext(a.audio)[1].lower() if a.audio else ".mp3")
    full = common.P(a.work, full_name)
    if a.audio and os.path.abspath(a.audio) != os.path.abspath(full):
        shutil.copyfile(a.audio, full)

    try:
        with open(common.P(a.work, "translations.json"), encoding="utf-8") as f:
            TR = {int(k): v for k, v in json.load(f).items()}
    except FileNotFoundError:
        TR = {}

    official = sum(1 for s in sents if s.get("src") == "official")

    # ---------------- CSV ----------------
    with open(common.P(a.work, "index.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["序号", "开始", "结束", "时长s", "板块", "说话人", "原文", "中文", "音频文件", "来源"])
        for i, s in enumerate(sents, 1):
            w.writerow([
                i, mmss(s["clip_start"]), mmss(s["clip_end"]),
                round(s["clip_end"] - s["clip_start"], 1),
                SECTION_CN.get(s.get("section"), s.get("section") or "考试说明"),
                speaker_of(s),
                s["text"], TR.get(i, ""), s.get("file", ""),
                "官方原文" if s.get("src") == "official" else "语音识别",
            ])

    # ---------------- Markdown ----------------
    lines = [f"# {TITLE}", "",
             f"- 总句数：**{len(sents)}**（其中 {official} 句与官方真题原文逐句对齐）",
             f"- 音频总长：{mmss(d['duration'])}",
             "- 音频片段：`audio_sentences/001.mp3` …"]
    cur_sec = None
    for i, s in enumerate(sents, 1):
        sec = s.get("section") or "Directions"
        if sec != cur_sec:
            cur_sec = sec
            lines += ["", f"## {SECTION_CN.get(sec, sec)}", "",
                      "| # | 时间 | 说话人 | 原文 |", "|---|---|---|---|"]
        txt = s["text"].replace("|", "\\|")
        lines.append(f"| {i} | {mmss(s['clip_start'])} | {speaker_of(s)} | {txt} |")
    with open(common.P(a.work, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # ---------------- HTML ----------------
    rows = []
    nav = []
    cur_sec = None
    gi = 0
    for i, s in enumerate(sents, 1):
        sec = s.get("section") or "Directions"
        if sec != cur_sec:
            cur_sec = sec
            gi += 1
            name = SECTION_CN.get(sec, sec)
            if nav and name in [n[1] for n in nav]:
                name = f"{name}（续）"
            nav.append((f"g{gi}", name))
            rows.append(f'</tbody></table></section><section class="grp"><h2 id="g{gi}">{common.esc(name)}'
                        f'<span class="sub">{common.esc(sec)}</span></h2><table><tbody>')
        spk = s.get("speaker")
        spk_cls = {"Man": "m", "Woman": "w", "Q": "q"}.get(spk, "x")
        verified = s.get("src") == "official" or s.get("section") == "Directions"
        rows.append(
            f'<tr id="s{i}" data-src="{common.esc(s.get("file", ""))}">'
            f'<td class="idx">{i}</td>'
            f'<td class="tm"><button class="play" title="播放本句">▶</button>'
            f'<span class="t">{mmss(s["clip_start"])}</span></td>'
            f'<td class="spk"><span class="bd {spk_cls}">{speaker_of(s)}</span></td>'
            f'<td class="tx">{common.esc(s["text"])}'
            + ('' if verified else ' <span class="warn" title="该句未能与官方原文匹配，文本来自语音识别">ASR</span>')
            + '</td></tr>'
        )
    body = "\n".join(rows)
    body = body.replace("</tbody></table></section>", "", 1) + "</tbody></table></section>"
    nav = "".join(f'<a href="#{a}">{common.esc(n)}</a>' for a, n in nav)
    safe_title = common.esc(TITLE)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title}</title>
<style>
:root{{--bg:#f7f8fa;--card:#fff;--bd:#e3e6ec;--tx:#1d2129;--tx2:#606670;--ac:#2f6feb;--ac2:#eaf1ff}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);
font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",Arial,sans-serif}}
.wrap{{max-width:960px;margin:0 auto;padding:28px 20px 80px}}
h1{{font-size:22px;margin:0 0 6px}}
.meta{{color:var(--tx2);font-size:13px;margin-bottom:18px}}
.bar{{position:sticky;top:0;z-index:5;background:var(--card);border:1px solid var(--bd);
border-radius:12px;padding:12px 14px;display:flex;gap:12px;align-items:center;margin-bottom:18px;
box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.bar audio{{flex:1;height:34px}}
.hint{{font-size:12px;color:var(--tx2);white-space:nowrap}}
.grp{{background:var(--card);border:1px solid var(--bd);border-radius:12px;
margin-bottom:14px;overflow:hidden}}
.grp h2{{font-size:15px;margin:0;padding:12px 16px;border-bottom:1px solid var(--bd);
background:#fbfcfe;display:flex;align-items:baseline;gap:8px}}
.grp h2 .sub{{font-weight:400;font-size:12px;color:var(--tx2)}}
table{{width:100%;border-collapse:collapse}}
tr{{border-bottom:1px solid #f0f2f5}}
tr:last-child{{border-bottom:none}}
tr:hover{{background:#fafbfe}}
tr.playing{{background:var(--ac2)}}
td{{padding:9px 12px;vertical-align:top}}
.idx{{width:44px;color:var(--tx2);font-size:13px;font-variant-numeric:tabular-nums}}
.tm{{width:92px;white-space:nowrap}}
.t{{color:var(--tx2);font-size:13px;font-variant-numeric:tabular-nums}}
.play{{border:1px solid var(--bd);background:#fff;color:var(--ac);border-radius:6px;
width:26px;height:26px;cursor:pointer;font-size:11px;line-height:1;margin-right:8px;vertical-align:middle}}
.play:hover{{background:var(--ac);color:#fff;border-color:var(--ac)}}
.spk{{width:56px}}
.bd{{display:inline-block;font-size:12px;padding:1px 8px;border-radius:20px;border:1px solid}}
.bd.m{{color:#1a56c4;border-color:#c3d6f7;background:#eef4ff}}
.bd.w{{color:#b4327a;border-color:#f5cfe3;background:#fdf0f6}}
.bd.q{{color:#8a6d1f;border-color:#ecdfb8;background:#fdf8e8}}
.bd.x{{color:#8c8c8c;border-color:#e3e3e3;background:#f5f5f5}}
.tx{{font-size:15px}}
.tip{{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#1d2129;color:#fff;
font-size:13px;padding:10px 16px;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.2);z-index:99;max-width:90%}}
.howto{{background:#fffbe9;border:1px solid #f2e3b3;border-radius:10px;padding:10px 14px;
font-size:13px;color:#7a5c10;margin-bottom:16px}}
.nav{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}}
.nav a{{font-size:12px;color:var(--ac);background:#fff;border:1px solid var(--bd);
border-radius:16px;padding:3px 12px;text-decoration:none}}
.nav a:hover{{background:var(--ac);color:#fff;border-color:var(--ac)}}
.warn{{font-size:11px;color:#b4327a;background:#fdf0f6;border:1px solid #f5cfe3;
border-radius:4px;padding:0 4px;margin-left:4px;vertical-align:1px}}
</style></head><body><div class="wrap">
<h1>{safe_title}</h1>
<div class="meta">共 {len(sents)} 句 · 音频总长 {mmss(d['duration'])} · {official} 句已与官方真题原文逐句对齐 · 点击 ▶ 播放单句</div>
<div class="howto">本页依赖同目录音频：请保留 <code>index.html</code>、<code>{common.esc(full_name)}</code> 和 <code>audio_sentences/</code>。想独立携带练习材料，请打开生成的<b>单文件版 HTML</b>。键盘：<b>↓</b> 下一句 / <b>↑</b> 上一句 / <b>空格</b> 重播。</div>
<div class="bar"><audio id="full" controls preload="none" src="{common.esc(full_name)}"></audio>
<span class="hint">整段音频</span></div>
<div class="nav">{nav}</div>
{body}
</div>
<div class="tip" id="tip" hidden></div>
<script>
const tipEl=document.getElementById('tip');let tipT=null;
function tip(m){{tipEl.textContent=m;tipEl.hidden=false;clearTimeout(tipT);
  tipT=setTimeout(()=>tipEl.hidden=true,7000);}}
const aud=new Audio();let cur=null;
aud.onerror=()=>{{tip('音频加载失败：请确认 index.html 与 audio_sentences 文件夹在同一个目录下（不要只把 index.html 单独拷走）。');}};
const full=document.getElementById('full');
full.onerror=()=>{{tip('整段音频 full.mp3 未找到，单句播放不受影响。');}};
document.addEventListener('click',e=>{{
  const b=e.target.closest('.play');if(!b)return;
  const tr=b.closest('tr');const f=tr.dataset.src;if(!f)return;
  full.pause();
  if(cur===tr&&!aud.paused){{aud.pause();tr.classList.remove('playing');b.textContent='▶';return;}}
  document.querySelectorAll('tr.playing').forEach(x=>{{x.classList.remove('playing');
    const bb=x.querySelector('.play');if(bb)bb.textContent='▶';}});
  aud.src='audio_sentences/'+f;tr.classList.add('playing');b.textContent='■';cur=tr;
  aud.onended=()=>{{tr.classList.remove('playing');b.textContent='▶';}};
  aud.play().catch(err=>{{tip('播放失败：'+err.message+'。请用电脑浏览器打开单文件版 HTML。');}});
}});
// 快捷键：↓ 下一句 / ↑ 上一句 / 空格 重播当前句
document.addEventListener('keydown',e=>{{
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
  const rows=[...document.querySelectorAll('tr[data-src]')];
  let i=rows.indexOf(cur);
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){{
    e.preventDefault();
    i = (i<0)?0 : i + (e.key==='ArrowDown'?1:-1);
    i=Math.max(0,Math.min(rows.length-1,i));
    rows[i].scrollIntoView({{block:'center'}});rows[i].querySelector('.play').click();
  }} else if(e.key===' '&&cur){{e.preventDefault();cur.querySelector('.play').click();}}
}});
</script></body></html>"""

    out_html = common.P(a.work, a.out or "index.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {len(sents)} 句 -> {out_html} / index.csv / index.md")


if __name__ == "__main__":
    main()
