from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import Statevector
from qiskit import transpile
from scipy.optimize import minimize
from src.classical import cut_value
import numpy as np

def build_qaoa(H, p):
    circuit = QAOAAnsatz(cost_operator=H, reps=p)
    return transpile(circuit, basis_gates=["h", "rx", "rz", "rzz"], optimization_level=0)

def hamiltonian_diagonal(H):
    return H.to_matrix(sparse=True).diagonal().real

# calculez <H> pentru unghiurile date ------------------
# params: lista de unghiuri [beta, gamma]
def energy(params, circuit, diagonal):
    """Energy of the QAOA state: probability of each bitstring times its energy."""
    state = Statevector(circuit.assign_parameters(params))
    probabilities = state.probabilities()
    return float(np.dot(probabilities, diagonal))

# generez "harta" cu unghiurile beta is gamma ------------------
def energy_landscape(circuit, diagonal, betas, gammas):
    energies = np.zeros((len(betas), len(gammas)))
    for i, beta in enumerate(betas):
        for j, gamma in enumerate(gammas):
            energies[i, j] = energy([beta, gamma], circuit, diagonal)
    return energies


# functia de warm start ------------------
def warm_start(params):
    """Starting point for p + 1 layers from the best angles for p layers:
    the new layer gets beta = 0 and gamma = 0, so it does nothing at first."""
    p = len(params) // 2
    betas = list(params[:p])
    gammas = list(params[p:])
    return betas + [0.0] + gammas + [0.0]


# optimizez qaoa - pentru p >= 1 ------------------
def optimize_qaoa(H, p, num_starts=10, seed=42, initial_params=None):
    circuit = build_qaoa(H, p)
    diagonal = hamiltonian_diagonal(H)
    rng = np.random.default_rng(seed)

    # toate punctele de start
    starts = []
    for _ in range(num_starts):
        start_betas = rng.uniform(0, np.pi/2, p)
        start_gammas = rng.uniform(0, np.pi, p)
        starts.append(np.concatenate([start_betas, start_gammas]))

    if initial_params is not None:
        starts.append(np.array(initial_params))

    best_params = None
    best_energy = None

    for start in starts:
        res = minimize(energy, start, args=(circuit, diagonal), method="COBYLA", options={"maxiter": 200})

        if best_energy is None or best_energy > res.fun:
            best_energy = res.fun
            best_params = res.x

    return best_energy, best_params

# calculez metricile ------------------------------------
def all_cuts(graph):
    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"
    cuts_list = []

    for i in range(2 ** n):
        bitstring = format(i, binary_format)
        cuts_list.append(cut_value(graph, bitstring))

    return np.array(cuts_list)

def qaoa_metrics(graph, problem, probabilities, optimal_bitstrings, num_samples=4000, seed=42):
    """Metrics of a probability distribution over bitstrings, for one graph and problem:
    valid_fraction, mean_cut (over valid bitstrings), p_optimal and the best cut among
    num_samples simulated shots. Metrics that need valid bitstrings are NaN if there are none."""
    n = graph.number_of_nodes()
    cuts = all_cuts(graph)

    # valid bitstrings: all of them for Max-Cut, only the balanced ones for bisection
    if problem == "maxcut":
        valid = np.ones(2 ** n, dtype=bool)
    else:
        k = np.arange(2 ** n)
        ones = sum((k >> i) & 1 for i in range(n))       # number of 1s in each bitstring
        valid = (ones == n // 2) | (n - ones == n // 2)

    # total probability of the valid bitstrings
    valid_fraction = np.sum(probabilities[valid])

    # average cut, over the valid bitstrings only (NaN if there are none)
    if valid_fraction > 0:
        mean_cut = np.sum(probabilities[valid] * cuts[valid]) / valid_fraction
    else:
        mean_cut = np.nan

    # probability of measuring an optimal solution
    p_optimal = sum(probabilities[int(bitstring, 2)] for bitstring in optimal_bitstrings)

    # best cut among num_samples simulated shots (valid shots only; NaN if there are none)
    rng = np.random.default_rng(seed)
    samples = rng.choice(2 ** n, size=num_samples, p=probabilities / np.sum(probabilities))
    valid_samples = samples[valid[samples]]
    if len(valid_samples) == 0:
        best_sample_cut = np.nan
    elif problem == "maxcut":
        best_sample_cut = np.max(cuts[valid_samples])     # Max-Cut: the larger the better
    else:
        best_sample_cut = np.min(cuts[valid_samples])     # bisection: the smaller the better

    return {
        "valid_fraction": float(valid_fraction),
        "mean_cut": float(mean_cut),
        "p_optimal": float(p_optimal),
        "best_sample_cut": float(best_sample_cut),
    }