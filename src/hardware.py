import json
from datetime import datetime, timezone
import os
from qiskit.transpiler import generate_preset_pass_manager 
from src.qaoa import build_qaoa

# verific ce porti din setul de operatii folosesc porti cu 2 qubiti
def get_two_qubit_gate(backend):
    for name in backend.target.operation_names:
        operation = backend.target.operation_from_name(name)
        if operation.num_qubits == 2:
            return name

    return None

# am nevoie de un snapshot al calibrarii pentru backend
def calibration_snapshot(backend):
    """The current calibration data of the backend, as a dictionary."""
    target = backend.target
    gate_2q = get_two_qubit_gate(backend)

    # intr o lista de qubiti iau toate detaliile despre ei
    qubits = []
    for q in range(backend.num_qubits):
        properties = backend.qubit_properties(q)
        qubits.append({
            "qubit": q,
            "t1": properties.t1,
            "t2": properties.t2,
            "readout_error": target["measure"][(q,)].error,
            "sx_error": target["sx"][(q,)].error,
        })

    # perechile de qubiti
    pairs = []
    for qubit_pair, properties in target[gate_2q].items():
        pairs.append({
            "qubits": list(qubit_pair),
            "error": properties.error,
        })

    return {
        "backend": backend.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "two_qubit_gate": gate_2q,
        "qubits": qubits,
        "pairs": pairs,
    }


# salvez snapshot-ul sub format json
def save_calibration_snapshot(backend, folder="../data/qpu/calibration"):
    """Save the current calibration of the backend as a JSON file; return its path."""
    snapshot = calibration_snapshot(backend)
    time_tag = snapshot["timestamp"][:16].replace(":", "-")

    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, backend.name + "_" + time_tag + ".json")
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)

    return path


# trebuie sa compar backend urile si sa vad pe care il aleg: iau mediana si nu media erorilor de citire
import numpy as np
import pandas as pd

def backend_summary(backend):
    target = backend.target
    gate = get_two_qubit_gate(backend)

    # errors of the two-qubit gate, over all coupled pairs
    errors_2q = [props.error for props in target[gate].values()
                 if props is not None and props.error is not None]

    # readout errors, over all qubits -----> de rescris in forma larga, sa inteleg si eu cum se pun termenii
    errors_readout = [props.error for props in target["measure"].values()
                      if props is not None and props.error is not None]

    # coherence times, over all qubits (in microseconds)
    t1 = []
    t2 = []
    for q in range(backend.num_qubits):
        qp = backend.qubit_properties(q)
        if qp.t1 is not None:
            t1.append(qp.t1 * 1e6)
        if qp.t2 is not None:
            t2.append(qp.t2 * 1e6)

    # connectivity: how many neighbours each qubit has
    neighbours = {}
    for a, b in target[gate].keys():
        neighbours.setdefault(a, set()).add(b)
    max_degree = max(len(s) for s in neighbours.values())

    return {
        "name": backend.name,
        "qubits": backend.num_qubits,
        "gate_2q": gate,
        "median_2q_error": np.median(errors_2q),
        "median_readout_error": np.median(errors_readout),
        "median_t1_us": np.median(t1),
        "median_t2_us": np.median(t2),
        "max_degree": max_degree,
        "pending_jobs": backend.status().pending_jobs,
    }


# partea de transpile
def transpile_best(circuit, backend, seeds=(0, 1, 2, 3, 4), optimization_level=3):
    """Transpile with several seeds; keep the result with the fewest two-qubit gates."""
    # 1. the name of the two-qubit gate on this backend
    gate_2q = get_two_qubit_gate(backend)

    # 2. "best so far": nothing yet
    best = None
    best_count = None
    best_seed = None

    # 3. try every seed
    for seed in seeds:
        pass_manager = generate_preset_pass_manager(backend=backend, optimization_level=optimization_level, seed_transpiler=seed)
        transpiled = pass_manager.run(circuit)
        count = transpiled.count_ops().get(gate_2q, 0)

        if best is None or count < best_count:
            best = transpiled
            best_count = count
            best_seed = seed

    # 4. the winner
    return best, best_seed



def transpile_qaoa_best(H, p, params, backend, seeds=(0, 1, 2, 3, 4)):
    """Build the QAOA circuit with the terms of H in two orders (original and sorted),
    transpile each with several seeds, and keep the one with the fewest two-qubit gates."""
    gate_2q = get_two_qubit_gate(backend)
    best = None
    best_count = None
    best_seed = None
    best_order = None

    for order, hamiltonian in [("original", H), ("sorted", H.sort())]:
        circuit = build_qaoa(hamiltonian, p).assign_parameters(params)
        circuit.measure_all()
        transpiled, seed = transpile_best(circuit, backend, seeds)
        count = transpiled.count_ops().get(gate_2q, 0)

        if best is None or count < best_count:
            best = transpiled
            best_count = count
            best_seed = seed
            best_order = order

    return best, best_seed, best_order







def estimated_success(transpiled, backend):
    """Probability that no gate and no readout fails, from the backend calibration."""
    target = backend.target
    probability = 1.0

    for instruction in transpiled.data:
        name = instruction.operation.name
        if name not in target.operation_names:
            continue                       # e.g. barrier: not a physical operation
        qubits = tuple(transpiled.find_bit(q).index for q in instruction.qubits)
        properties = target[name].get(qubits)
        if properties is not None and properties.error is not None:
            probability *= 1 - properties.error

    return probability







def counts_to_probabilities(counts, n):
    """Turn a counts dictionary {bitstring: count} into a probability vector of length 2^n,
    indexed like Statevector.probabilities() (bitstring read as a binary number)."""
    probabilities = np.zeros(2 ** n)
    shots = sum(counts.values())
    for bitstring, count in counts.items():
        probabilities[int(bitstring, 2)] = count / shots
    return probabilities