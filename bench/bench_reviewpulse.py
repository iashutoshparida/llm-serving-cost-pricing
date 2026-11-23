"""Benchmark an OpenAI-compatible endpoint (vLLM) on the ReviewPulse workload.

Measures two things for one model:
1. Quality: theme-tagging micro F1 on the SemEval-2014 restaurant test set,
   using the same prompt as ReviewPulse's Gemini tagger, so results are
   directly comparable with ReviewPulse v3 (0.878 micro F1).
2. Speed: aggregate output tokens/s and p50/p95 latency at a fixed
   concurrency, with ReviewPulse-sized prompts.

Appends one row to results/benchmarks.csv. The workbook input A2
(throughput) is then replaced with the measured value.

    python bench/bench_reviewpulse.py --base-url http://localhost:8000/v1 \
        --model Qwen/Qwen2.5-7B-Instruct-AWQ --gpu "T4 (Colab)" --quant awq
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import statistics
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import httpx

THEMES = ["food", "service", "price", "ambience"]
TEST_URL = ("https://raw.githubusercontent.com/davidsbatista/Aspect-Based-Sentiment-Analysis/"
            "master/datasets/ABSA-SemEval2014/Restaurants_Test_Data_phaseB.xml")
PROMPT = """You tag restaurant review sentences with themes.
Themes: food (food, drinks, menu, portions), service (staff, speed, orders, delivery),
price (cost, value, bill), ambience (atmosphere, decor, noise, seating, cleanliness).
A sentence can have zero, one or several themes. Return JSON only:
a list with one object per sentence, in order: {{"i": <index>, "themes": [...]}}.

Sentences:
{items}"""
BATCH = 25
OUT = Path(__file__).resolve().parents[1] / "results" / "benchmarks.csv"


def load_test():
    xml = urllib.request.urlopen(TEST_URL, timeout=60).read()
    rows = []
    for s in ET.fromstring(xml).iter("sentence"):
        cats = {c.get("category") for c in s.iter("aspectCategory")}
        rows.append((s.findtext("text"), [int(t in cats) for t in THEMES]))
    return rows


async def call(client, args, items):
    t0 = time.perf_counter()
    r = await client.post(f"{args.base_url}/chat/completions", json={
        "model": args.model, "temperature": 0, "max_tokens": 600,
        "messages": [{"role": "user", "content": PROMPT.format(items=items)}],
    })
    r.raise_for_status()
    body = r.json()
    return body, time.perf_counter() - t0


def parse(text, n):
    pred = [[0] * 4 for _ in range(n)]
    try:
        start, end = text.index("["), text.rindex("]") + 1
        for obj in json.loads(text[start:end]):
            i = int(obj.get("i", -1))
            if 0 <= i < n:
                for t in obj.get("themes", []):
                    if t in THEMES:
                        pred[i][THEMES.index(t)] = 1
    except (ValueError, json.JSONDecodeError, AttributeError):
        pass
    return pred


def micro_f1(y, p):
    tp = sum(a and b for yy, pp in zip(y, p) for a, b in zip(yy, pp))
    fp = sum((not a) and b for yy, pp in zip(y, p) for a, b in zip(yy, pp))
    fn = sum(a and (not b) for yy, pp in zip(y, p) for a, b in zip(yy, pp))
    return 2 * tp / (2 * tp + fp + fn) if tp else 0.0


async def main(args):
    data = load_test()
    batches = [data[i:i + BATCH] for i in range(0, len(data), BATCH)]
    sem = asyncio.Semaphore(args.concurrency)
    results = [None] * len(batches)
    out_tokens, latencies = 0, []

    async with httpx.AsyncClient(timeout=300) as client:
        async def run(k, b):
            nonlocal out_tokens
            async with sem:
                items = "\n".join(f"{i}. {s}" for i, (s, _) in enumerate(b))
                body, dt = await call(client, args, items)
                latencies.append(dt)
                out_tokens += body.get("usage", {}).get("completion_tokens", 0)
                results[k] = parse(body["choices"][0]["message"]["content"], len(b))

        t0 = time.perf_counter()
        await asyncio.gather(*(run(k, b) for k, b in enumerate(batches)))
        wall = time.perf_counter() - t0

    y = [lab for _, lab in data]
    p = [row for r in results for row in r]
    lat = sorted(latencies)
    row = {
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "gpu": args.gpu, "model": args.model, "quantization": args.quant,
        "concurrency": args.concurrency, "sentences": len(data),
        "micro_f1": round(micro_f1(y, p), 3),
        "output_tokens_per_sec": round(out_tokens / wall, 1),
        "p50_latency_s": round(statistics.median(lat), 2),
        "p95_latency_s": round(lat[int(0.95 * (len(lat) - 1))], 2),
        "wall_seconds": round(wall, 1),
    }
    OUT.parent.mkdir(exist_ok=True)
    new = not OUT.exists() or OUT.stat().st_size == 0
    with OUT.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--gpu", required=True)
    ap.add_argument("--quant", default="none")
    ap.add_argument("--concurrency", type=int, default=16)
    asyncio.run(main(ap.parse_args()))
