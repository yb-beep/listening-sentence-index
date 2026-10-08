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
import hashlib
import glob
import json
import os
import subprocess
import sys
import time

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


def read_config(work):
    try:
        with open(os.path.join(work, "config.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(work, cfg):
    path = os.path.join(work, "config.json")
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)
    os.replace(path + ".tmp", path)


def input_signature(cfg):
    sig = {"model": cfg.get("model") or "large-v3-turbo", "lang": cfg.get("lang") or "en"}
    for key in ("audio", "ref"):
        path = cfg.get(key)
        if not path:
            sig[key] = None
            continue
        path = os.path.abspath(os.path.expanduser(path))
        digest = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for block in iter(lambda: f.read(1024 * 1024), b""):
                    digest.update(block)
            sig[key] = {"path": path, "sha256": digest.hexdigest()}
        except OSError:
            sig[key] = {"path": path, "missing": True}
    return sig


def artifacts_ready(step, work, cfg):
    """完成记录必须和实际产物一致；仅 config.json 存在不能表示音频或网页仍在。"""
    try:
        if step in ("align.py", "fill_gaps.py", "split.py"):
            with open(os.path.join(work, "sentences.json"), encoding="utf-8") as f:
                sents = json.load(f)["sentences"]
            if not sents:
                return False
            if step == "split.py":
                dep_time = max(os.path.getmtime(p) for p in
                               [os.path.join(HERE, "split.py"), os.path.join(HERE, "common.py"),
                                cfg.get("audio") or os.path.join(work, "sentences.json")])
                return all(s.get("clip_end", 0) > s.get("clip_start", 0)
                           and os.path.getsize(os.path.join(work, "audio_sentences", s.get("file", ""))) > 0
                           and os.path.getmtime(os.path.join(work, "audio_sentences", s.get("file", ""))) >= dep_time
                           for s in sents)
            return True
        if step == "make_single.py":
            title = cfg.get("title") or "逐句精听索引"
            for c in '/\\:*?"<>|':
                title = title.replace(c, "_")
            path = os.path.join(work, (title.strip() or "index") + "（单文件版）.html")
        else:
            path = os.path.join(work, ARTIFACT[step])
        if not os.path.isfile(path) or not os.path.getsize(path):
            return False
        if step in ("build_index.py", "make_single.py"):
            deps = [os.path.join(work, name) for name in
                    ("sentences.json", "translations.json", "sections.json")]
            deps += [os.path.join(HERE, step), os.path.join(HERE, "common.py")]
            if step == "make_single.py":
                deps.append(os.path.join(HERE, "page_tpl.py"))
            return all(os.path.getmtime(path) >= os.path.getmtime(p)
                       for p in deps if os.path.exists(p))
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


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
    p.add_argument("--lang", default=None)
    p.add_argument("--only", default=None,
                   help="只跑某一步，如 --only split.py；也支持逗号分隔多步")
    p.add_argument("--skip", default="", help="跳过某几步，逗号分隔")
    p.add_argument("--resume", action="store_true",
                   help="续跑：跳过 config.json 里记录的已完成步骤")
    p.add_argument("--restart", action="store_true",
                   help="忽略已有产物，从头重做（会清掉已记录的步骤）")
    a = p.parse_args()

    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    steps = [s.strip() for s in a.only.split(",") if s.strip()] if a.only else STEPS
    if not steps or any(s not in STEPS for s in [*steps, *skip]):
        p.error("--only / --skip 只能选择流水线中列出的脚本")

    work = os.path.abspath(os.path.expanduser(a.work))
    os.makedirs(work, exist_ok=True)

    cfg = read_config(work)
    old_title = cfg.get("title")
    old_sig = cfg.get("pipeline_signature")
    if a.audio and cfg.get("audio") and not a.ref:
        if os.path.abspath(os.path.expanduser(a.audio)) != os.path.abspath(os.path.expanduser(cfg["audio"])):
            cfg.pop("ref", None)
    for key in ("audio", "ref", "title", "model", "lang"):
        value = getattr(a, key)
        if value:
            cfg[key] = os.path.abspath(os.path.expanduser(value)) if key in ("audio", "ref") else value
    sig = input_signature(cfg)
    changed = old_sig is not None and old_sig != sig
    restart = bool(a.restart or os.environ.get("LSI_RESTART") or changed)
    if changed:
        print("输入音频、原文或识别设置已改变：重新制作，旧译文先保存到备份目录。")
        previous = os.path.join(work, "_previous_inputs", str(time.time_ns()))
        translations = glob.glob(os.path.join(work, "_trans_*.json"))
        translations += [os.path.join(work, "translations.json")]
        for path in translations:
            if os.path.isfile(path):
                os.makedirs(previous, exist_ok=True)
                os.replace(path, os.path.join(previous, os.path.basename(path)))
    if restart or old_sig is None:
        cfg["done_steps"] = []
    elif a.title and a.title != old_title:
        cfg["done_steps"] = sorted(set(cfg.get("done_steps", [])) - {"build_index.py", "make_single.py"})
    cfg["pipeline_signature"] = sig
    save_config(work, cfg)

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
    if restart:
        extra += ["--restart"]

    done = read_done(work) if (a.resume and not restart) else set()
    if done:
        print(f"续跑模式：已完成 {', '.join(sorted(done))}")

    for s in steps:
        if s in skip:
            print(f"· 跳过 {s}")
            continue
        if s in done and artifacts_ready(s, work, read_config(work)):
            print(f"· {s} 上次已完成，跳过（想重做加 --restart）")
            continue
        # 上游重新运行后，下游完成记录随即失效，即使本次在上游失败也不会误跳过。
        invalid = set(STEPS[STEPS.index(s):])
        done.difference_update(invalid)
        current = read_config(work)
        current["done_steps"] = sorted(set(current.get("done_steps", [])) - invalid)
        save_config(work, current)
        run(s, extra)
        art = ARTIFACT.get(s)
        if art and not os.path.exists(os.path.join(work, art)):
            # 典型情况：transcribe 没跑完（转写到一半就停了），下游还不能开始
            print(f"\n⏸ {s} 还没做完：{art} 未生成。\n"
                  f"  重新执行同一条命令，会从断点继续。", flush=True)
            sys.exit(1)
        if not artifacts_ready(s, work, read_config(work)):
            print(f"\n⏸ {s} 的产物缺失或不完整，请检查后续跑。", flush=True)
            sys.exit(1)
        write_done(work, s)

    if artifacts_ready("make_single.py", work, read_config(work)):
        print("\n所选步骤已完成。主交付物：工作目录下的「<标题>（单文件版）.html」，"
              "用电脑浏览器打开即可练习。", flush=True)
    else:
        print("\n所选步骤已完成；中间产物在工作目录。运行剩余步骤后生成单文件版 HTML。", flush=True)


if __name__ == "__main__":
    main()
