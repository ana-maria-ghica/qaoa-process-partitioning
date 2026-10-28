import networkx as nx
import numpy as np

from src.hamiltonians import max_cut_hamiltonian
from src.qaoa import build_qaoa, hamiltonian_diagonal, energy, warm_start, qaoa_metrics


# warm start adds one layer with angles 0: [b1, g1] -> [b1, 0, g1, 0]
def test_warm_start():
    assert warm_start([0.3, 0.7]) == [0.3, 0.0, 0.7, 0.0]
    assert len(warm_start([0.1, 0.2, 0.3, 0.4])) == 6


# with all angles 0 the state stays a uniform superposition, so the energy is the mean of the diagonal
def test_energy_at_zero_angles():
    H = max_cut_hamiltonian(nx.cycle_graph(6))
    circuit = build_qaoa(H, 1)
    diagonal = hamiltonian_diagonal(H)
    assert np.isclose(energy([0.0, 0.0], circuit, diagonal), diagonal.mean())


# the warm start does not change the energy: p + 1 layers with a zero layer = p layers
def test_warm_start_keeps_energy():
    H = max_cut_hamiltonian(nx.cycle_graph(6))
    diagonal = hamiltonian_diagonal(H)
    params = [0.4, 0.8]
    e1 = energy(params, build_qaoa(H, 1), diagonal)
    e2 = energy(warm_start(params), build_qaoa(H, 2), diagonal)
    assert np.isclose(e1, e2)


# hand-computed example: one edge, bisection, probabilities of 00, 01, 10, 11
def test_metrics_hand_example():
    graph = nx.Graph([(0, 1)])
    metrics = qaoa_metrics(graph, "bisection", np.array([0.1, 0.4, 0.3, 0.2]), ["01", "10"])
    assert np.isclose(metrics["valid_fraction"], 0.7)
    assert metrics["mean_cut"] == 1.0
    assert np.isclose(metrics["p_optimal"], 0.7)
    assert metrics["best_sample_cut"] == 1.0


# no balanced bitstring at all: the metrics that need one are nan, not an error
def test_metrics_no_valid_bitstrings():
    graph = nx.cycle_graph(6)
    probabilities = np.zeros(2 ** 6)
    probabilities[0] = 1.0
    metrics = qaoa_metrics(graph, "bisection", probabilities, ["010101"])
    assert metrics["valid_fraction"] == 0
    assert np.isnan(metrics["mean_cut"])
    assert np.isnan(metrics["best_sample_cut"])
