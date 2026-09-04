# -*- coding: utf-8 -*-
"""measurement_utils.py — bootstrap CI and inter-annotator agreement (Cohen's kappa)."""
import random


def bootstrap_ci(values, iters=2000, seed=42, ci=0.95):
    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(iters):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    lo = sorted(means)[int((1 - ci) / 2 * iters)]
    hi = sorted(means)[int((1 + ci) / 2 * iters) - 1]
    return {"mean": round(sum(values) / n, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
            "n": n, "iters": iters}


def cohen_kappa(a, b):
    """Cohen's kappa for two raters on categorical labels.

    a and b are equal-length lists of labels.
    """
    if len(a) != len(b) or not a:
        return None
    categories = sorted(set(a) | set(b))
    n = len(a)
    # observed agreement
    o = sum(1 for x, y in zip(a, b) if x == y) / n
    # expected agreement
    counts_a = {c: a.count(c) for c in categories}
    counts_b = {c: b.count(c) for c in categories}
    e = sum((counts_a[c] / n) * (counts_b[c] / n) for c in categories)
    if e == 1:
        return 1.0
    return round((o - e) / (1 - e), 4)
