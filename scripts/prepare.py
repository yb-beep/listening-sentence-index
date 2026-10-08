#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并安装依赖：faster-whisper / av(PyAV) / numpy。
不装 ffmpeg —— PyAV 自带 mp3 编码器（libmp3lame）。

    python prepare.py                       # 只检查
    python prepare.py --install             # 缺什么装什么

国内网络可指定镜像：
    PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple python prepare.py --install
模型走 hf-mirror：export HF_ENDPOINT=https://hf-mirror.com
"""
import argparse
import importlib
import os
import subprocess
import sys

NEED = {"faster_whisper": "faster-whisper", "av": "av", "numpy": "numpy"}


def have(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true", help="自动 pip 安装缺失依赖")
    ap.add_argument("--index-url", default=os.environ.get("PIP_INDEX_URL"))
    a = ap.parse_args()

    missing = [p for m, p in NEED.items() if not have(m)]
    if not missing:
        print("依赖齐全：faster-whisper / av / numpy 均已安装。")
        return
    print("缺少依赖：", ", ".join(missing))
    if not a.install:
        print("加 --install 自动安装（或用你习惯的 pip 命令手动装）。")
        sys.exit(1)

    cmd = [sys.executable, "-m", "pip", "install"] + missing
    if a.index_url:
        cmd += ["--index-url", a.index_url]
    print("执行：", " ".join(cmd), flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0 and not a.index_url:
        print("\n安装失败。国内机器可换镜像重试，例如：\n"
              "  PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple \\\n"
              "  python prepare.py --install")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
