# LLM serving cost & pricing model for ReviewPulse

**Should an AI feature call a hosted model API or self-host an open model on a GPU, and what should it charge?** This repo answers that for [ReviewPulse](https://github.com/iashutoshparida/reviewpulse), a review-insights tool for small restaurants, with a live-formula Excel model, a Python mirror with tests, a vLLM benchmark notebook, and the decision memo.

## The answer

**Use the hosted API now. Self-hosting only wins at about 1.55 million reviews a month (~15,500 restaurants).** Price on willingness to pay, not on serving cost.

| | Value | Where it comes from |
|---|---|---|
| Tokens per review (tag + reply draft) | 511 in, 224 out | Measured ReviewPulse workload on 10,000 Yelp reviews |
| Gemini 3.1 Flash-Lite, per 1,000 reviews | **$0.46** | List price × tokens |
| Same, per restaurant-month (100 reviews) | **≈ INR 3.9** | |
| One L4 VM always on, plus 8 h/month upkeep | **≈ $719 / month** | GCP g2-standard-8 on-demand list price |
| Break-even vs Flash-Lite | **≈ 1.55M reviews / month** (0.74M on spot) | Fixed cost ÷ API cost per review |
| Break-even if we needed Gemini 3.6 Flash | ≈ 294,000 reviews / month | API at 5.3x the Flash-Lite cost |
| Gross margin, Starter (INR 299) / Pro (INR 799) | **88% / 93%** | COGS = API + WhatsApp + hosting + gateway fee |

The finding that shaped the decision: **GPU throughput lowers the marginal cost per review but does not move break-even**, which depends only on the GPU's fixed monthly cost and the API price. Throughput decides whether one GPU can even reach that volume. At 300 tokens/s it can't.

Full reasoning: [decision memo](docs/decision_memo.md).

## What's measured and what's assumed

| Input | Status |
|---|---|
| Review length, sentences per review | Measured in ReviewPulse |
| API, GPU, WhatsApp and payment-gateway prices | Cited list prices, checked 23 Nov 2026 (sources in the Inputs sheet) |
| GPU throughput (A2), prompt overhead (A4) | **Assumed** until `bench/vllm_benchmark_colab.ipynb` is run |
| Chars per token (A1) | **Assumed** until real Gemini usage is logged |
| Tier prices, CAC, churn | **Hypotheses** for the willingness-to-pay survey ([pricing research](docs/pricing_research.md)) |

Assumptions are yellow cells in the workbook. Changing any of them updates every sheet.

## Contents

- `model/serving_cost_pricing.xlsx`: Inputs (with sources), API vs Self-host, Pricing (unit economics and CAC payback), Sensitivity
- `src/costmodel.py`: Python mirror of the workbook (`python src/costmodel.py`)
- `src/vanwestendorp.py`: price-sensitivity analysis for the owner survey
- `bench/vllm_benchmark_colab.ipynb` + `bench/bench_reviewpulse.py`: serve an open 7-8B model with vLLM on a Colab GPU and measure theme-tagging F1 (same test set as ReviewPulse) and output tokens/s. Results go to `results/benchmarks.csv`.
- `docs/decision_memo.md`, `docs/pricing_research.md`, `docs/risk_register.md`
- `build_workbook.py`: regenerates the workbook

## Run

```bash
pip install -r requirements.txt
python src/costmodel.py
pytest -q tests
python build_workbook.py     # rebuild the xlsx (open in Excel to recalculate)
```
