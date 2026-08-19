# benchmark.py
# compares local STT engines (whisper sizes vs vosk) on TTS-generated samples
#
# usage:
#   python benchmark.py <audio_dir> [engine ...]
#     engine specs: whisper:tiny whisper:base whisper:small whisper:medium
#                   whisper:large-v3-turbo vosk:en vosk:ru vosk:pl
#     (no engine args = run all light engines: vosk x3 + tiny/base/small)
#
# measures per engine: cold model load time, warm per-file transcription time,
# word error rate (WER) against known ground truth, and peak process RAM.
# each engine runs in its own child process (isolated memory measurement).
# requires psutil for the RAM measurement: pip install psutil

import json
import re
import subprocess
import sys
import time

AUDIO_LANGS = ("en", "ru", "pl")

GROUND_TRUTH = {
    "en": "Hello my friend, stay a while and listen. The zone is very dangerous today, watch out for anomalies.",
    "ru": "Привет друг, как дела? Осторожно, рядом мутанты и аномалии.",
    "pl": "Witaj przyjacielu, jak sie masz? Uwazaj na anomalie w strefie.",
}

DEFAULT_ENGINES = ["vosk:en", "vosk:ru", "vosk:pl",
                   "whisper:tiny", "whisper:tiny.en",
                   "whisper:base", "whisper:base.en",
                   "whisper:small", "whisper:small.en"]
ENGINE_TIMEOUT_S = 900  # per-engine hard kill


################################################################################################
# WER
################################################################################################

def _normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return text.split()


def _levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def wer(reference, hypothesis):
    ref, hyp = _normalize(reference), _normalize(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return _levenshtein(ref, hyp) / len(ref)


################################################################################################
# CHILD: run one engine, print JSON
################################################################################################

def run_child(engine, audio_dir):
    kind, param = engine.split(":", 1)

    import logging
    import threading
    logging.basicConfig(level=logging.ERROR)

    # peak RAM self-sampling (cross-process queries are unreliable in sandboxes)
    import psutil
    peak = {"rss": 0}
    _self = psutil.Process()

    def _sampler():
        while True:
            try:
                peak["rss"] = max(peak["rss"], _self.memory_info().rss)
            except psutil.Error:
                break
            time.sleep(0.02)

    threading.Thread(target=_sampler, daemon=True).start()

    result = {"engine": engine, "kind": kind, "param": param}

    if kind == "whisper":
        import whisper_local
        whisper_local.configure(model_size=param, prefer_en_variant=False)
        langs = ("en",) if param.endswith(".en") else AUDIO_LANGS
        t0 = time.perf_counter()
        model = whisper_local.get_model()          # cold load (downloads on first ever run)
        result["load_s"] = round(time.perf_counter() - t0, 2)
        result["model"] = getattr(model, "model_size", param)
        for lang in langs:
            path = f"{audio_dir}/{lang}.ogg"
            t0 = time.perf_counter()
            text = whisper_local.transcribe_audio_file(path, prompt="", lang=lang)
            result[f"{lang}_s"] = round(time.perf_counter() - t0, 2)
            result[f"{lang}_wer"] = round(wer(GROUND_TRUTH[lang], text), 4)
            result[f"{lang}_text"] = text
    elif kind == "vosk":
        import vosk_local
        from languages import vosk_model_info
        lang = param
        info = vosk_model_info(lang)
        result["model"] = info[0] if info else None
        t0 = time.perf_counter()
        vosk_local.get_model(lang)                 # cold load (downloads on first ever run)
        result["load_s"] = round(time.perf_counter() - t0, 2)
        path = f"{audio_dir}/{lang}.ogg"
        t0 = time.perf_counter()
        text = vosk_local.transcribe_audio_file(path, prompt="", lang=lang)
        result[f"{lang}_s"] = round(time.perf_counter() - t0, 2)
        result[f"{lang}_wer"] = round(wer(GROUND_TRUTH[lang], text), 4)
        result[f"{lang}_text"] = text
    else:
        raise ValueError(f"unknown engine kind: {kind}")

    time.sleep(0.1)  # let the sampler catch the final peak
    result["peak_rss_mb"] = round(peak["rss"] / 1048576)
    print("BENCH_JSON " + json.dumps(result, ensure_ascii=False))


################################################################################################
# PARENT: spawn children, sample RAM, build table
################################################################################################

def run_engine_isolated(engine, audio_dir):
    import threading
    cmd = [sys.executable, "-X", "utf8", __file__, "--child", engine, audio_dir]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")

    output = []

    def reader():
        for line in proc.stdout:
            line = line.rstrip()
            output.append(line)
            print(f"    [{engine}] {line[:120]}")

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    deadline = time.time() + ENGINE_TIMEOUT_S
    while proc.poll() is None:
        if time.time() > deadline:
            print(f"    [{engine}] TIMEOUT after {ENGINE_TIMEOUT_S}s - killing")
            proc.kill()
            break
        time.sleep(0.05)
    proc.wait()
    thread.join(timeout=5)

    result = None
    for line in output:
        if line.startswith("BENCH_JSON "):
            result = json.loads(line[len("BENCH_JSON "):])
    if result is None:
        result = {"engine": engine, "error": "no result (crashed or timed out)",
                  "output_tail": output[-5:]}
    return result


def fmt_cell(result, key):
    v = result.get(key)
    return "-" if v is None else f"{v}"


def main():
    args = sys.argv[1:]
    if args and args[0] == "--child":
        run_child(args[1], args[2])
        return

    audio_dir = args[0] if args else "."
    engines = args[1:] if len(args) > 1 else DEFAULT_ENGINES

    print(f"Benchmarking {len(engines)} engines on samples in {audio_dir}")
    results = []
    for engine in engines:
        print(f"  running {engine} ...")
        results.append(run_engine_isolated(engine, audio_dir))

    print()
    print("| Engine | Load (s) | EN s | EN WER | RU s | RU WER | PL s | PL WER | Peak RAM (MB) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        if "error" in r:
            print(f"| {r['engine']} | FAILED | {r['error'][:60]} | | | | | | {r.get('peak_rss_mb', '-')} |")
            continue
        cells = [r.get("model") or r["engine"], fmt_cell(r, "load_s"),
                 fmt_cell(r, "en_s"), fmt_cell(r, "en_wer"),
                 fmt_cell(r, "ru_s"), fmt_cell(r, "ru_wer"),
                 fmt_cell(r, "pl_s"), fmt_cell(r, "pl_wer"),
                 fmt_cell(r, "peak_rss_mb")]
        print("| " + " | ".join(cells) + " |")

    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nRaw results (incl. transcribed texts) written to benchmark_results.json")


if __name__ == "__main__":
    main()
