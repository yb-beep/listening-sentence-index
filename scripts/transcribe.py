#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 1：用 faster-whisper 转写整段音频，输出带词级时间戳的 segments_raw.json。

支持断点续传：音频先按「停顿处」切成若干小块，每转写完一块就立刻落盘记账。
中断后再跑同一条命令，会自动跳过已完成的部分，从断开的那一块继续。

用法：
    python transcribe.py --work ./out --audio ./listen.mp3
    python transcribe.py --work ./out --audio ./listen.mp3 --model small   # 慢机器/长音频
    python transcribe.py --work ./out --limit 4        # 这次只转 4 块（分批推进）
    python transcribe.py --work ./out --restart        # 丢弃进度，从头重转
"""
import json
import os
import sys
import time

import av
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # noqa: E402
import common  # noqa: E402

from faster_whisper import WhisperModel  # noqa: E402

TARGET = 45.0   # 每块目标时长（秒）
MAXLEN = 90.0   # 常规单块上限；不足半秒的尾部并入末块，避免漏音
MINSIL = 0.20   # 允许下刀的最短静音（秒）

# 模型别名。turbo 是 large-v3 的蒸馏版：CPU 上比 large-v3 快 5~8 倍，
# 英文听力的字错率几乎持平，是我们默认的推荐。想要极致准确率就 --model large-v3。
MODEL_ALIAS = {
    "turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
}

DEFAULT_PROMPT = (
    "This is an English listening comprehension recording. "
    "It may contain conversations, passages, lectures, announcements and questions. "
    "Transcribe exactly what is spoken, with punctuation."
)


def decode_16k(src):
    """解码 + 重采样到 16kHz 单声道 int16（whisper 要求的输入规格）"""
    container = av.open(src)
    stream = container.streams.audio[0]
    rs = av.AudioResampler(format="s16", layout="mono", rate=16000)
    parts = []
    for frame in container.decode(stream):
        for f in rs.resample(frame):
            parts.append(f.to_ndarray().reshape(-1))
    for f in rs.resample(None):                      # flush
        parts.append(f.to_ndarray().reshape(-1))
    container.close()
    return np.concatenate(parts).astype(np.int16), 16000


def plan_chunks(pcm, sr, target=TARGET, maxlen=MAXLEN, minsil=MINSIL):
    """
    在【静音处】把音频切成块。切点永远落在停顿里，所以不会把句子拦腰砍断。
    切分只依赖音频本身 -> 同样的音频重跑会得到完全一样的切点，这是续传能对齐的前提。
    """
    mono = pcm.astype(np.float32) / 32768.0
    rms, win = common.compute_rms(mono, sr)
    thr = max(0.0015, float(np.percentile(rms, 50)) * 0.10)
    dur = len(pcm) / sr
    need = max(1, int(minsil / win))
    chunks = []
    start = 0.0
    while start < dur:
        i0 = int((start + target) / win)
        i1 = min(len(rms), int((start + maxlen) / win))
        cut = None
        if i1 > i0:
            cold = rms[i0:i1] < thr
            i = 0
            while i < len(cold):
                if cold[i]:
                    j = i
                    while j < len(cold) and cold[j]:
                        j += 1
                    if (j - i) >= need:
                        cut = (i0 + (i + j) // 2) * win      # 取这段静音的中点
                        break
                    i = j
                else:
                    i += 1
        if cut is None or cut <= start + 1.0:
            cut = min(dur, start + maxlen)
        cut = min(cut, dur)
        if dur - cut < 0.5:
            cut = dur
        chunks.append((round(start, 3), round(cut, 3)))
        start = cut
        if cut >= dur:
            break
    return chunks


_W = {}   # 子进程里的模型与配置


def _init_worker(model_path, opts):
    from faster_whisper import WhisperModel
    m = WhisperModel(model_path, device="cpu", compute_type="int8",
                     cpu_threads=opts["threads"])
    if opts["batch"]:
        try:
            from faster_whisper import BatchedInferencePipeline
            _W["runner"] = BatchedInferencePipeline(model=m)
            _W["batch_size"] = opts["batch_size"]
        except Exception:
            _W["runner"] = m
    else:
        _W["runner"] = m
    _W["opts"] = opts


def _run_chunk(task):
    """处理一块音频，返回 (块序号, [segment...])"""
    import numpy as np
    k, s, e, buf, sr = task
    audio = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
    o = _W["opts"]
    kw = {"batch_size": _W["batch_size"]} if "batch_size" in _W else {}
    segs, _info = _W["runner"].transcribe(
        audio, language=o["lang"], beam_size=5, word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=350, speech_pad_ms=120),
        condition_on_previous_text=False, initial_prompt=o["prompt"], **kw)
    rows = []
    for seg in segs:
        rows.append({
            "start": round(s + seg.start, 3),
            "end": round(s + seg.end, 3),
            "text": seg.text.strip(),
            "words": [{"w": w.word.strip(), "s": round(s + w.start, 3),
                       "e": round(s + w.end, 3)} for w in (seg.words or [])],
        })
    return k, rows


def load_progress(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    a = common.get_args("转写音频为带词级时间戳的 JSON（支持断点续传）")
    prog_path = common.P(a.work, "transcribe_progress.json")
    partial = common.P(a.work, "segments_raw.jsonl")
    final = common.P(a.work, a.out or "segments_raw.json")
    restart = a.restart
    limit = a.limit

    t0 = time.time()
    print("解码音频 ...", flush=True)
    pcm, sr = decode_16k(a.audio)
    duration = len(pcm) / sr
    chunks = plan_chunks(pcm, sr)
    print(f"  {duration:.1f}s -> 切成 {len(chunks)} 块（平均 "
          f"{duration/max(1,len(chunks)):.0f}s/块）", flush=True)

    sig = {"audio": a.audio, "size": os.path.getsize(a.audio),
           "mtime_ns": os.stat(a.audio).st_mtime_ns,
           "duration": round(duration, 3), "n_chunks": len(chunks), "model": a.model,
           "lang": a.lang, "prompt": os.environ.get("LSI_PROMPT", DEFAULT_PROMPT)}
    prog = load_progress(prog_path)
    done = 0
    if prog and os.path.exists(partial) and not restart and prog.get("sig") == sig:
        done = min(int(prog.get("done", 0)), len(chunks))
        if done:
            print(f"  发现上次进度：已完成 {done}/{len(chunks)} 块，从第 {done+1} 块继续"
                  f"（想从头重来加 --restart）", flush=True)
    else:
        if prog and restart:
            print("  --restart：丢弃旧进度", flush=True)
        open(partial, "w", encoding="utf-8").close()
        prog = {"sig": sig, "done": 0, "committed_bytes": 0}

    # 崩溃可能发生在写入一块的结果后、提交进度前。截去未提交的尾部，
    # 避免续跑把这一块重复写入；同时移除旧的完成标记，防止下游误用旧文件。
    if "committed_bytes" in prog:
        if os.path.getsize(partial) < prog["committed_bytes"]:
            done = 0
            prog.update(done=0, committed_bytes=0)
        with open(partial, "r+b") as fh:
            fh.truncate(prog["committed_bytes"])
    if os.path.exists(final):
        os.remove(final)

    def commit_progress(fh, completed):
        fh.flush()
        prog["done"] = completed
        prog["committed_bytes"] = os.path.getsize(partial)
        temp = prog_path + ".tmp"
        with open(temp, "w", encoding="utf-8") as pf:
            json.dump(prog, pf, ensure_ascii=False, indent=1)
        os.replace(temp, prog_path)

    model_path = MODEL_ALIAS.get(a.model, a.model)
    jobs = max(1, int(getattr(a, "jobs", 1) or 1))
    use_batch = not getattr(a, "no_batch", False)
    end_at = len(chunks) if limit is None else min(len(chunks), done + max(0, limit))
    # 并行要每个进程各加载一份模型（十几秒），块太少时不划算。
    # 经验阈值：剩余块数至少是进程数的 2 倍才开并行，否则自动退回单进程。
    need = jobs * 2
    parallel = jobs > 1 and (end_at - done) >= need
    if jobs > 1 and not parallel:
        print(f"  只剩 {end_at - done} 块，少于 {need} 块，并行不划算 -> 改用单进程", flush=True)

    # 批量推理：把一段里的多句话打包一起过模型，CPU 上通常还能再快一截
    batch_kw = {}
    runner = None
    if not parallel:      # 并行时由子进程各自加载，父进程不必占用内存
        model = WhisperModel(model_path, device="cpu", compute_type="int8", cpu_threads=8)
        if use_batch:
            try:
                from faster_whisper import BatchedInferencePipeline
                runner = BatchedInferencePipeline(model=model)
                batch_kw["batch_size"] = max(1, int(getattr(a, "batch_size", 8)))
                print(f"  启用批量推理 batch_size={batch_kw['batch_size']}", flush=True)
            except Exception as e:
                runner = model
                print(f"  批处理不可用（{e}），退回逐段推理", flush=True)
        else:
            runner = model
        print(f"model loaded in {time.time()-t0:.1f}s  [{model_path}]", flush=True)
    else:
        print(f"  并行模式：{jobs} 个进程同时转写  [{model_path}]", flush=True)

    opts = {
        "threads": max(1, 8 // max(1, jobs)), "batch": use_batch,
        "batch_size": max(1, int(getattr(a, "batch_size", 8))),
        "lang": a.lang, "prompt": os.environ.get("LSI_PROMPT", DEFAULT_PROMPT),
    }
    wrote = 0
    with open(partial, "a", encoding="utf-8") as fh:
        if parallel:
            from concurrent.futures import ProcessPoolExecutor
            tasks = [(k, chunks[k][0], chunks[k][1],
                      pcm[int(chunks[k][0] * sr):int(chunks[k][1] * sr)].tobytes(), sr)
                     for k in range(done, end_at)]
            finished = 0
            with ProcessPoolExecutor(max_workers=jobs, initializer=_init_worker,
                                     initargs=(model_path, opts)) as ex:
                for k, rows in ex.map(_run_chunk, tasks):
                    for r in rows:
                        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                    fh.flush()
                    wrote += len(rows)
                    commit_progress(fh, k + 1)
                    finished += 1
                    s0, e0 = chunks[k]
                    print(f"  块 {k+1}/{len(chunks)}  [{s0:.0f}s-{e0:.0f}s] -> "
                          f"{len(rows)} 段  ({finished}/{len(tasks)} done, "
                          f"{time.time()-t0:.0f}s elapsed)", flush=True)
        else:
            for k in range(done, end_at):
                s, e = chunks[k]
                seg_audio = pcm[int(s * sr):int(e * sr)].astype(np.float32) / 32768.0
                segs, _info = runner.transcribe(
                    seg_audio,
                    language=a.lang,
                    beam_size=5,
                    word_timestamps=True,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=350, speech_pad_ms=120),
                    condition_on_previous_text=False,
                    initial_prompt=os.environ.get("LSI_PROMPT", DEFAULT_PROMPT),
                    **batch_kw,
                )
                cnt = 0
                for seg in segs:
                    # 词时间戳是相对本块的，直接加块起点偏移
                    words = [{"w": w.word.strip(),
                              "s": round(s + w.start, 3),
                              "e": round(s + w.end, 3)}
                             for w in (seg.words or [])]
                    fh.write(json.dumps({
                        "start": round(s + seg.start, 3),
                        "end": round(s + seg.end, 3),
                        "text": seg.text.strip(),
                        "words": words,
                    }, ensure_ascii=False) + "\n")
                    cnt += 1
                fh.flush()
                wrote += cnt
                commit_progress(fh, k + 1)
                print(f"  块 {k+1}/{len(chunks)}  [{s:.0f}s-{e:.0f}s] -> {cnt} 段"
                      f"  ({time.time()-t0:.0f}s elapsed)", flush=True)

    total_done = prog["done"]
    if total_done < len(chunks):
        print(f"\n本次推进到第 {total_done}/{len(chunks)} 块，还没转完。"
              f"再次执行同一条命令即可从第 {total_done+1} 块接着跑。", flush=True)
        return

    rows = []
    with open(partial, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    rows.sort(key=lambda x: (x["start"], x["end"]))
    for i, r in enumerate(rows, 1):
        r["id"] = i
    with open(final, "w", encoding="utf-8") as f:
        json.dump({"duration": duration, "audio": a.audio, "segments": rows},
                  f, ensure_ascii=False, indent=1)
    try:
        os.remove(prog_path)
        os.remove(partial)
    except OSError:
        pass
    print(f"\nDONE {len(rows)} segments（本次新增 {wrote}），"
          f"total {time.time()-t0:.0f}s -> {final}")


if __name__ == "__main__":
    main()
