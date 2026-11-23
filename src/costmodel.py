"""Serving cost and pricing model for ReviewPulse (Python mirror of the workbook).

Question: should ReviewPulse call a hosted model API or self-host an open
7-8B model on one NVIDIA L4, and what should it charge?

Every input below is either a cited list price, a number measured in the
ReviewPulse repo, or a labelled assumption (A*) to be replaced by data.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

HOURS_PER_MONTH = 730

# ---- Workload, measured in ReviewPulse (results/eval_results.json) -------
AVG_REVIEW_CHARS = 710          # 10,000 Yelp reviews
AVG_SENTENCES = 9.5
CHARS_PER_TOKEN = 4             # A1: English average, replace with real usage


def tokens_per_review(draft_reply: bool = True) -> tuple[float, float]:
    review = AVG_REVIEW_CHARS / CHARS_PER_TOKEN
    tin = review + 120 * AVG_SENTENCES / 25
    tout = 12 * AVG_SENTENCES
    if draft_reply:
        tin += 110 + review
        tout += 110
    return tin, tout


# ---- Cited prices (checked 23 Nov 2026) -----------------------------------
API_PRICES = {  # USD per 1M tokens (input, output), ai.google.dev pricing page
    "Gemini 3.1 Flash-Lite": (0.25, 1.50),
    "Gemini 3.6 Flash (from Jan 2027)": (1.50, 7.50),
}
L4_HOURLY = {   # GCP g2-standard-8 (1x L4), cloud.google.com accelerator-optimized pricing
    "on-demand": 0.853624312,
    "spot": 0.340572,
}


@dataclass
class SelfHost:
    gpu_hourly: float = L4_HOURLY["on-demand"]
    out_tokens_per_sec: float = 800.0   # A2: aggregate decode throughput; replace with bench results
    utilization: float = 0.40           # A3: share of hours the GPU is busy
    prefill_overhead: float = 1.25      # A4: extra time for prompt processing
    ops_hours_per_month: float = 8.0    # A5: engineer time to run it
    ops_hourly_usd: float = 12.0        # A6: loaded cost of that time
    always_on: bool = True

    def capacity_reviews_per_month(self, tout: float) -> float:
        per_hour = self.out_tokens_per_sec * 3600 * self.utilization / (tout * self.prefill_overhead)
        return per_hour * HOURS_PER_MONTH

    def fixed_usd_per_month(self) -> float:
        return self.gpu_hourly * HOURS_PER_MONTH + self.ops_hours_per_month * self.ops_hourly_usd

    def marginal_usd_per_review(self, tout: float) -> float:
        """GPU cost per review when it is busy, ignoring idle time."""
        per_hour = self.out_tokens_per_sec * 3600 / (tout * self.prefill_overhead)
        return self.gpu_hourly / per_hour


def api_usd_per_review(model: str, draft_reply: bool = True) -> float:
    tin, tout = tokens_per_review(draft_reply)
    pin, pout = API_PRICES[model]
    return tin / 1e6 * pin + tout / 1e6 * pout


def breakeven_reviews_per_month(model: str, sh: SelfHost) -> float:
    """Monthly volume at which an always-on GPU costs the same as the API."""
    return sh.fixed_usd_per_month() / api_usd_per_review(model)


# ---- Pricing (INR) ---------------------------------------------------------
USD_INR = 84.0                 # A7: planning rate
WHATSAPP_UTILITY_INR = 0.115   # Meta India rate card from 1 Oct 2026, before GST
GATEWAY_FEE = 0.0236           # Razorpay standard 2% + 18% GST


@dataclass
class Tier:
    name: str
    price_inr: float              # H1: price hypotheses, to test with the WTP survey
    reviews_per_month: int        # A8: reviews processed per customer
    whatsapp_msgs_per_month: int
    hosting_inr: float = 25.0     # A9: share of app hosting per customer

    def cogs_inr(self, model: str = "Gemini 3.1 Flash-Lite") -> float:
        api = api_usd_per_review(model) * self.reviews_per_month * USD_INR
        return api + self.whatsapp_msgs_per_month * WHATSAPP_UTILITY_INR * 1.18 + self.hosting_inr + self.price_inr * GATEWAY_FEE

    def gross_margin(self, model: str = "Gemini 3.1 Flash-Lite") -> float:
        return 1 - self.cogs_inr(model) / self.price_inr if self.price_inr else float("nan")


TIERS = [
    Tier("Free", 0, 30, 0, hosting_inr=10),
    Tier("Starter", 299, 100, 4),
    Tier("Pro", 799, 300, 30),
]


def payback_months(tier: Tier, cac_inr: float, monthly_churn: float) -> float:
    contribution = tier.price_inr - tier.cogs_inr()
    return cac_inr / contribution if contribution > 0 else float("inf")


if __name__ == "__main__":
    tin, tout = tokens_per_review()
    print(f"tokens per review: in {tin:.0f}, out {tout:.0f}")
    for m in API_PRICES:
        print(f"{m}: ${api_usd_per_review(m)*1000:.3f} per 1k reviews")
    for label, rate in L4_HOURLY.items():
        for tps in (300, 800, 1500):
            sh = SelfHost(gpu_hourly=rate, out_tokens_per_sec=tps)
            print(f"L4 {label} {tps} tok/s: marginal ${sh.marginal_usd_per_review(tout)*1000:.3f}/1k, fixed ${sh.fixed_usd_per_month():.0f}/mo, "
                  f"capacity {sh.capacity_reviews_per_month(tout)/1e6:.2f}M/mo, breakeven vs Flash-Lite {breakeven_reviews_per_month('Gemini 3.1 Flash-Lite', sh)/1e6:.2f}M, "
                  f"vs Flash {breakeven_reviews_per_month('Gemini 3.6 Flash (from Jan 2027)', sh)/1e6:.2f}M")
    for t in TIERS:
        print(t.name, round(t.cogs_inr(), 1), round(t.gross_margin(), 3) if t.price_inr else "-")
