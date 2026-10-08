#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键跑完整条流水线（顺序不能乱）：

    transcribe.py -> align.py -> fill_gaps.py -> split.py -> build_index.py -> make_single.py

用法：
    python run_all.py --work ./out --audio ./listen.mp3 --ref ./script.txt --title "我的材料"
    python run_all.py --work ./out --audio ./listen.mp3 --model small      # 无原文、小模型

说明：
    * align.py 会重写 sentences.json，fill_gaps.py 的补识别结果必须在它【之后】跑，
      否则补回来的句子会被覆盖掉（句数会缩水）。
    * build_index.py 产出依赖同目录 audio_sentences/ 的外部音频版 index.html；
      make_single.py 产出音频内嵌的单文件版，两者都需要，单文件版是主交付物。
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["transcribe.py", "align.py", "fill_gaps.py", "split.py",
         "build_index.py", "make_single.py"]

# 产物存在与否 = 这一步做没做完
ARTIFACT = {
    "transcribe.py": "segments_raw.json",   # 没转完时这个文件不会出现
    "align.py": "sentences.json",
    "fill_gaps.py": None,                   # 有就补、没得补也算完成
    "split.py": None,
    "build_index.py": "index.html",
    "make_single.py": None,
}


def read_done(work):
    cfg = os.path.join(work, "config.json")
    try:
        with open(cfg, encoding="utf-8") as f:
            return set(json.load(f).get("done_steps") or [])
    except Exception:
        return set()


def write_done(work, step):
    cfg = os.path.join(work, "config.json")
    d = {}
    if os.path.exists(cfg):
        try:
            with open(cfg, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            d = {}
    done = set(d.get("done_steps") or [])
    done.add(step)
    d["done_steps"] = sorted(done)
    with open(cfg, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def run(step, extra):
    cmd = [sys.executable, os.path.join(HERE, step)] + extra
    print("\n" + "=" * 68 + f"\n▶ {step}  {' '.join(extra)}\n" + "=" * 68, flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"\n✗ {step} 失败（退出码 {r.returncode}），流水线中止。\n"
              f"  修好后重新执行同一条命令即可从这一步继续。", flush=True)
        sys.exit(r.returncode)


def main():
    p = argparse.ArgumentParser(description="一键生成逐句精听索引")
    p.add_argument("--work", default=os.environ.get("LSI_WORK", "."))
    p.add_argument("--audio", default=os.environ.get("LSI_AUDIO"))
    p.add_argument("--ref", default=None, help="官方原文 txt（可选）")
    p.add_argument("--title", default=None)
    p.add_argument("--model", default=None)
    p.add_argument("--lang", default="en")
    p.add_argument("--only", default=None,
                   help="只跑某一步，如 --only split.py；也支持逗号分隔多步")
    p.add_argument("--skip", default="", help="跳过某几步，逗号分隔")
    p.add_argument("--resume", action="store_true",
                   help="续跑：跳过 config.json 里记录的已完成步骤")
    p.add_argument("--restart", action="store_true",
                   help="忽略已有产物，从头重做（会清掉已记录的步骤）")
    a = p.parse_args()

    work = os.path.abspath(os.path.expanduser(a.work))
    os.makedirs(work, exist_ok=True)

    extra = ["--work", work]
    if a.audio:
        extra += ["--audio", a.audio]
    if a.ref:
        extra += ["--ref", a.ref]
    if a.title:
        extra += ["--title", a.title]
    if a.model:
        extra += ["--model", a.model]
    if a.lang:
        extra += ["--lang", a.lang]
    restart = a.restart or os.environ.get("LSI_RESTART")
    if restart:
        extra += ["--restart"]

    done = read_done(work) if (a.resume and not restart) else set()
    if done:
        print(f"续跑模式：已完成 {', '.join(sorted(done))}")

    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    steps = [s.strip() for s in a.only.split(",")] if a.only else STEPS
    for s in steps:
        if s in skip:
            print(f"· 跳过 {s}")
            continue
        if s in done and os.path.exists(os.path.join(work, ARTIFACT[s] or "config.json")):
            print(f"· {s} 上次已完成，跳过（想重做加 --restart）")
            continue
        run(s, extra)
        art = ARTIFACT.get(s)
        if art and not os.path.exists(os.path.join(work, art)):
            # 典型情况：transcribe 没跑完（转写到一半就停了），下游还不能开始
            print(f"\n⏸ {s} 还没做完：{art} 未生成。\n"
                  f"  重新执行同一条命令，会从断点继续。", flush=True)
            sys.exit(1)
        write_done(work, s)

    print("\n全部完成。主交付物：工作目录下的「<标题>（单文件版）.html」，"
          "双击即可播放，可任意拷贝/发给别人。", flush=True)


if __name__ == "__main__":
    main()
