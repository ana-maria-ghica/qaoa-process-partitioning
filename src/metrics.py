from src.graphs import find_instance, json_to_graph
from src.classical import max_cut_bruteforce, bisection_bruteforce
from src.qaoa import qaoa_metrics
from src.hardware import counts_to_probabilities
import numpy as np


import pandas as pd

def score(mean_cut, optimum, random_mean):
    """Normalized score S: 0 = as good as random guessing, 1 = optimal,
    negative = worse than random. NaN when optimum == random_mean (up to
    rounding), e.g. bisection on complete graphs, where S is undefined.
    Works on single numbers, numpy arrays and pandas columns."""
    denominator = random_mean - optimum
    zero = np.isclose(denominator, 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = (random_mean - mean_cut) / denominator
    if isinstance(result, pd.Series):
        return result.mask(zero)
    if np.ndim(result) > 0:
        return np.where(zero, np.nan, result)
    return np.nan if zero else float(result)



def metrics_from_counts(instances, name, problem, counts):
    """Metrics of measured bitstrings (QPU or random), plus the optimum,
    for one instance and problem."""
    # the problem: graph, optimum and all optimal bitstrings
    graph = json_to_graph(find_instance(instances, name))
    if problem == "maxcut":
        optimum, optimal_bitstrings = max_cut_bruteforce(graph)
    else:
        optimum, optimal_bitstrings = bisection_bruteforce(graph)

    # counts {bitstring: number} -> probability vector -> the same metrics as on the simulator
    probabilities = counts_to_probabilities(counts, graph.number_of_nodes())
    metrics = qaoa_metrics(graph, problem, probabilities, optimal_bitstrings)
    metrics["optimum"] = optimum
    return metrics


# functia de bootstrap
def bootstrap_metrics(instances, name, problem, counts, random_mean,
                      n_resamples=1000, seed=0):
    """Point estimates and 95% bootstrap confidence intervals for the metrics
    of measured bitstrings (QPU or random), including the score S.

    Resampling the shots with replacement is the same as drawing new counts
    from a multinomial over the unique bitstrings, so all resamples are made
    in one numpy call and the brute force runs only once per circuit."""
    rng = np.random.default_rng(seed)

    # the problem: graph, optimum and all optimal bitstrings (computed once)
    graph = json_to_graph(find_instance(instances, name))
    n = graph.number_of_nodes()
    if problem == "maxcut":
        optimum, optimal_bitstrings = max_cut_bruteforce(graph)
    else:
        optimum, optimal_bitstrings = bisection_bruteforce(graph)
    optimal_set = set(optimal_bitstrings)

    # one entry per unique measured bitstring
    bitstrings = list(counts.keys())
    times = np.array(list(counts.values()))
    num_shots = times.sum()

    cuts, valid, optimal = [], [], []
    for b in bitstrings:
        # bit i of the graph = b[-1 - i] (the same convention as cut_value)
        cut = sum(d.get("weight", 1) for u, v, d in graph.edges(data=True)
                  if b[-1 - u] != b[-1 - v])
        cuts.append(cut)
        valid.append(problem == "maxcut" or b.count("0") == n // 2)
        optimal.append(b in optimal_set)
    cuts = np.array(cuts, dtype=float)
    valid = np.array(valid, dtype=float)
    optimal = np.array(optimal, dtype=float)

    # all resamples at once: shape (n_resamples, number of unique bitstrings)
    resampled = rng.multinomial(num_shots, times / num_shots, size=n_resamples)
    # the original counts as row 0, so point estimates use the same formulas
    W = np.vstack([times, resampled]).astype(float)

    valid_shots = W @ valid
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_cut = (W @ (cuts * valid)) / valid_shots     # mean over valid shots
    valid_fraction = valid_shots / num_shots
    p_optimal = (W @ optimal) / num_shots
    S = score(mean_cut, optimum, random_mean)              # NaN if denominator is 0

    result = {"name": name, "problem": problem, "optimum": optimum}
    for key, v in {"mean_cut": mean_cut, "valid_fraction": valid_fraction,
                   "p_optimal": p_optimal, "score": S}.items():
        result[key] = v[0]                                  # point estimate
        result[key + "_lo"] = np.nanpercentile(v[1:], 2.5)  # 95% CI
        result[key + "_hi"] = np.nanpercentile(v[1:], 97.5)
    return result