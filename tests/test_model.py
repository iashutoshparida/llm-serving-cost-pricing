import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from costmodel import SelfHost, TIERS, api_usd_per_review, breakeven_reviews_per_month, tokens_per_review  # noqa: E402
from vanwestendorp import analyse  # noqa: E402


def test_tokens_match_workbook():
    tin, tout = tokens_per_review()
    assert round(tin, 1) == 510.6 and tout == 224


def test_api_cost_per_1k_reviews():
    assert abs(api_usd_per_review("Gemini 3.1 Flash-Lite") * 1000 - 0.464) < 0.001


def test_breakeven_independent_of_throughput():
    a = breakeven_reviews_per_month("Gemini 3.1 Flash-Lite", SelfHost(out_tokens_per_sec=300))
    b = breakeven_reviews_per_month("Gemini 3.1 Flash-Lite", SelfHost(out_tokens_per_sec=1500))
    assert a == b and 1.5e6 < a < 1.6e6


def test_paid_tiers_have_positive_margin():
    assert all(t.gross_margin() > 0.8 for t in TIERS if t.price_inr)


def test_van_westendorp_on_a_test_fixture():
    # Synthetic fixture for the test only; not survey data.
    rng = np.random.default_rng(0)
    base = rng.normal(400, 60, 200)
    df = pd.DataFrame({"too_cheap": base * 0.4, "cheap": base * 0.7,
                       "expensive": base * 1.3, "too_expensive": base * 1.8})
    r = analyse(df)
    assert r["point_of_marginal_cheapness"] < r["optimal_price_point"] < r["point_of_marginal_expensiveness"]
