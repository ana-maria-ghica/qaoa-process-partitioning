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

# functia propriu-zisa
def qaoa_metrics(graph, problem, probabilities, optimal_bitstrings, num_samples=4000, seed=42):
    n = graph.number_of_nodes()
    cuts = all_cuts(graph)

    # in functie de problema [max cut / bisection] selectez bitstring-urile valide
    valid = np.zeros(2 ** n, dtype=bool)
    binary_format = "0" + str(n) + "b"
    for k in range(2 ** n):
        if problem == "maxcut":
            valid[k] = True
        else:
            zeros = format(k, binary_format).count("0")
            ones = n - zeros
            if zeros == n//2 or ones == n//2:
                valid[k] = True

    # suma probabilitatilor bitstring-urilor valide
    valid_fraction = np.sum(probabilities[valid])

    # cat de buna este, in medie, taietura
    mean_cut = np.sum(probabilities[valid] * cuts[valid]) / valid_fraction

    # probabilitatea sa gasesc solutia optima
    p_optimal = 0
    for bitstring in optimal_bitstrings:
        p_optimal += probabilities[int(bitstring, 2)]

    # 4. best cut among num_samples simulated shots (valid shots only)
    rng = np.random.default_rng(seed)
    samples = rng.choice(2 ** n, size=num_samples, p=probabilities / np.sum(probabilities))
    valid_samples = samples[valid[samples]]
    if problem == "maxcut":
        best_sample_cut = np.max(cuts[valid_samples])
    else:
        best_sample_cut = np.min(cuts[valid_samples])

    return {
        "valid_fraction": float(valid_fraction),
        "mean_cut": float(mean_cut),
        "p_optimal": float(p_optimal),
        "best_sample_cut": float(best_sample_cut),
    }
