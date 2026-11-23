# Decision memo: serve ReviewPulse from a hosted API or a self-hosted GPU?

Author: Ashutosh Parida · 23 Nov 2026 · Status: decided for the pilot, revisit at the trigger below

## Decision

**Use the hosted API (Gemini 3.1 Flash-Lite) for the pilot and the first paid customers. Do not self-host.** Revisit when one of the triggers at the end is hit.

## Why

All numbers come from `model/serving_cost_pricing.xlsx` (mirrored in `src/costmodel.py`).

1. **The API is cheap at our scale.** One review (tag every sentence and draft a reply) uses about 511 input and 224 output tokens. At list price that is **$0.46 per 1,000 reviews**, or **about INR 3.9 a month** for a restaurant with 100 reviews.
2. **An always-on GPU has a high fixed cost.** One L4 VM (g2-standard-8) on demand costs about $623 a month. With 8 hours of engineer time for upkeep the total is **about $719 a month**, whether or not it is busy.
3. **Break-even is far away.** Self-hosting only beats the API above **about 1.55 million reviews a month**, roughly **15,500 restaurants** at 100 reviews each. A spot VM halves that to about 0.74 million, but spot machines can be pre-empted mid-digest.
4. **Throughput doesn't rescue it.** Faster serving lowers the marginal cost per review ($0.04–0.22 per 1,000 on demand) but does not move break-even, which depends only on fixed cost and the API price. Throughput only decides whether one GPU can reach that volume. At 300 output tokens/s it cannot: capacity is 1.13M reviews a month at 40% utilisation.
5. **The decision flips if the API price rises.** If we needed Gemini 3.6 Flash (about 5.3x the Flash-Lite cost from Jan 2027), break-even drops to about 294,000 reviews a month, roughly 2,900 restaurants. Model choice matters more than serving choice.

## What we give up

- Data stays with a third-party API. Mitigation: send review text only, no owner or customer personal data.
- Exposure to API price changes. Mitigation: the tagger interface takes any provider, and the benchmark notebook keeps an open-model fallback measured and ready.

## Pricing implication

COGS per paying customer is small: INR 36 a month for Starter (INR 299) and INR 60 for Pro (INR 799), a gross margin of 88–93%. The biggest COGS lines are the app-hosting share and the payment gateway fee, not AI (API cost is INR 3.9 on Starter and INR 11.7 on Pro). **Price should be set by what owners will pay, not by serving cost.** The willingness-to-pay survey in `docs/pricing_research.md` sets the final prices.

## Triggers to revisit

| Trigger | Why |
|---|---|
| > 500,000 reviews a month | Within 3x of spot break-even; start a self-host pilot |
| Quality requires a Flash-class model | Break-even falls to ~2,900 restaurants |
| A customer requires data to stay on our servers | Non-cost reason to self-host |
| Benchmark shows an open 7B AWQ model ≥ ReviewPulse v3 F1 (0.878) at ≥ 800 tok/s on L4 | Makes the self-host fallback credible |

## What is assumed, not measured

Yellow cells in the workbook: characters per token (A1), GPU throughput (A2), utilisation (A3), prompt overhead (A4), engineer time and cost (A5, A6), exchange rate (A7), tier prices and hosting share, CAC and churn. A2 and A4 get replaced by `bench/vllm_benchmark_colab.ipynb`, A1 by real Gemini usage data, and prices by the survey.
