#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把分批翻译的 _trans_*.json 合并成 translations.json。

约定：每个 _trans_N.json 是一个对象 {"1": "中文…", "2": "中文…"}，
键是句子序号（字符串或数字都行），值是中文译文。
多个文件里有同一个序号时，后合并的覆盖先合并的（按文件名排序）。

用法：
    python merge_translations.py --work ./out
    python merge_translations.py --work ./out --check      # 只检查缺哪几句
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402
import common  # noqa: E402

p = None  # 占位，避免静态检查误报


def main():
    a = common.get_args("合并分批译文", need_audio=False)
    d = common.load_sentences(a.work)
    n = len(d["sentences"])
    files = sorted(glob.glob(common.P(a.work, "_trans_*.json")))
    if not files:
        print(f"没找到 _trans_*.json。请按序号分批翻译，例如写 "
              f"{a.work}/_trans_1.json = {{\"1\":\"…\",\"2\":\"…\"}}", file=sys.stderr)
        sys.exit(1)
    tr = {}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            for k, v in json.load(fh).items():
                if str(v).strip():
                    tr[int(k)] = str(v).strip()
    missing = [i for i in range(1, n + 1) if not tr.get(i)]
    if "--check" in sys.argv:
        print(f"共 {n} 句，已译 {n - len(missing)} 句，缺 {len(missing)} 句")
        print("缺少的序号：", missing[:200], "…" if len(missing) > 200 else "")
        return
    with open(common.P(a.work, "translations.json"), "w", encoding="utf-8") as f:
        json.dump({str(k): tr[k] for k in sorted(tr)}, f, ensure_ascii=False, indent=1)
    print(f"已合并 {len(tr)} 条译文 -> translations.json（共 {n} 句，"
          f"缺 {len(missing)} 句）")
    if missing:
        print("缺少的序号：", missing[:100], "…" if len(missing) > 100 else "")


if __name__ == "__main__":
    main()
