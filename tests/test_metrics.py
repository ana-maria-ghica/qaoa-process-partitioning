import numpy as np
import pandas as pd

from src.graphs import build
from src.metrics import score, metrics_from_counts, bootstrap_metrics


# s = 0 at the random mean, 1 at the optimum, 0.5 halfway
def test_score_reference_points():
    assert score(3, 6, 3) == 0
    assert score(6, 6, 3) == 1
    assert score(4.5, 6, 3) == 0.5


# optimum == random mean (bisection on complete graphs): s is undefined, never inf
def test_score_undefined_is_nan():
    assert np.isnan(score(9, 9, 9))
    assert np.isnan(score(9.0000000001, 9, 9))
    column = score(pd.Series([4.5, 9.0000000001]), pd.Series([6, 9]), pd.Series([3, 9]))
    assert column.iloc[0] == 0.5
    assert np.isnan(column.iloc[1])


# the bootstrap point estimates must equal the plain metrics of the same counts
def test_bootstrap_matches_metrics():
    instances = build()
    counts = {"010101": 1500, "101010": 1400, "001011": 600, "000111": 500}
    plain = metrics_from_counts(instances, "ring_6", "maxcut", counts)
    boot = bootstrap_metrics(instances, "ring_6", "maxcut", counts, random_mean=3.0)
    for key in ["mean_cut", "valid_fraction", "p_optimal"]:
        assert np.isclose(plain[key], boot[key])
        assert boot[key + "_lo"] <= boot[key] <= boot[key + "_hi"]
