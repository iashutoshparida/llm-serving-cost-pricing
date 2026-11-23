"""Van Westendorp price sensitivity analysis for the owner WTP survey.

Input: CSV with one row per respondent and four prices in INR per month:
too_cheap, cheap, expensive, too_expensive (see docs/pricing_research.md).
Output: the acceptable price range (marginal cheapness to marginal
expensiveness) and the optimal price point, using the standard crossings:
too cheap x not cheap, too cheap x too expensive, cheap x expensive,
too expensive x not expensive.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd


def curves(df: pd.DataFrame, grid: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "price": grid,
        "too_cheap": [(df.too_cheap >= p).mean() for p in grid],
        "cheap": [(df.cheap >= p).mean() for p in grid],
        "expensive": [(df.expensive <= p).mean() for p in grid],
        "too_expensive": [(df.too_expensive <= p).mean() for p in grid],
        "not_cheap": [1 - (df.cheap >= p).mean() for p in grid],
        "not_expensive": [1 - (df.expensive <= p).mean() for p in grid],
    })


def crossing(c: pd.DataFrame, a: str, b: str) -> float:
    diff = (c[a] - c[b]).to_numpy()
    idx = np.where(np.diff(np.sign(diff)) != 0)[0]
    return float(c.price.iloc[idx[0] + 1]) if len(idx) else float("nan")


def analyse(df: pd.DataFrame, step: float = 10) -> dict:
    grid = np.arange(0, df.too_expensive.max() + step, step)
    c = curves(df, grid)
    return {
        "respondents": len(df),
        "point_of_marginal_cheapness": crossing(c, "too_cheap", "not_cheap"),
        "optimal_price_point": crossing(c, "too_cheap", "too_expensive"),
        "indifference_price_point": crossing(c, "cheap", "expensive"),
        "point_of_marginal_expensiveness": crossing(c, "too_expensive", "not_expensive"),
    }


if __name__ == "__main__":
    print(analyse(pd.read_csv(sys.argv[1])))
