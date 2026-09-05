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


def krippendorff_alpha(data, nominal=True):
    """Krippendorff's alpha for nominal data.

    `data` is a list of raters; each rater is a list of labels of the same length.
    Missing values should be None (treated as absent, not a category).
    Returns alpha in [-1, 1], or None if not computable.
    """
    if not data or len(data) < 2:
        return None
    n_items = len(data[0])
    if any(len(r) != n_items for r in data):
        return None
    n_raters = len(data)
    # value set
    values = sorted({v for r in data for v in r if v is not None})
    if len(values) < 2:
        return None

    # coincidence counts
    coincidence = {v: {w: 0 for w in values} for v in values}
    for item in range(n_items):
        present = [r[item] for r in data if r[item] is not None]
        for i in range(len(present)):
            for j in range(len(present)):
                if i != j:
                    coincidence[present[i]][present[j]] += 1
    # units and values total
    n_units = sum(sum(1 for r in data if r[i] is not None) for i in range(n_items))
    n_values = sum(sum(coincidence[v].values()) for v in values)

    if n_values <= 0:
        return None

    # observed disagreement
    do = 0
    for v in values:
        for w in values:
            if v != w:
                do += coincidence[v][w]
    do /= n_values

    # expected disagreement
    col_sums = {w: sum(coincidence[v][w] for v in values) for w in values}
    de = 0
    for w in values:
        de += col_sums[w] * (n_values - col_sums[w])
    if n_values <= 1:
        return None
    de /= (n_values * (n_values - 1))

    if de == 0:
        return 1.0 if do == 0 else 0.0
    return round(1 - (do / de), 4)
