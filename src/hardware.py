import json
from datetime import datetime, timezone
import os

import numpy as np
import pandas as pd
from qiskit import qpy
from qiskit.transpiler import generate_preset_pass_manager

from src.qaoa import build_qaoa


# name of the backend's native two-qubit gate (e.g. "cz")
def get_two_qubit_gate(backend):
    for name in backend.target.operation_names:
        if backend.target.operation_from_name(name).num_qubits == 2:
            return name
    return None


# calibrated error of an operation on given qubits, or None if the backend has no value for it
def _error(target, operation, qubits):
    if operation not in target.operation_names:
        return None
    properties = target[operation].get(qubits)
    return properties.error if properties is not None else None


# current calibration of the backend: t1, t2, readout and sx error per qubit, error per coupled pair
# missing values are stored as None instead of crashing
def calibration_snapshot(backend):
    target = backend.target
    gate_2q = get_two_qubit_gate(backend)

    qubits = []
    for q in range(backend.num_qubits):
        properties = backend.qubit_properties(q)
        qubits.append({
            "qubit": q,
            "t1": properties.t1 if properties is not None else None,
            "t2": properties.t2 if properties is not None else None,
            "readout_error": _error(target, "measure", (q,)),
            "sx_error": _error(target, "sx", (q,)),
        })

    pairs = []
    for qubit_pair, properties in target[gate_2q].items():
        pairs.append({
            "qubits": list(qubit_pair),
            "error": properties.error if properties is not None else None,
        })

    return {
        "backend": backend.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "two_qubit_gate": gate_2q,
        "qubits": qubits,
        "pairs": pairs,
    }


# saves the snapshot as json, named after the backend and the time; returns the path
def save_calibration_snapshot(backend, folder="../data/qpu/calibration"):
    snapshot = calibration_snapshot(backend)
    time_tag = snapshot["timestamp"][:16].replace(":", "-")

    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, backend.name + "_" + time_tag + ".json")
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)
    return path


# one row for the backend comparison: medians over the whole chip, so a few broken qubits don't skew it
def backend_summary(backend):
    target = backend.target
    gate = get_two_qubit_gate(backend)

    # errors of the two-qubit gate, over all coupled pairs
    errors_2q = []
    for properties in target[gate].values():
        if properties is not None and properties.error is not None:
            errors_2q.append(properties.error)

    # readout errors, over all qubits
    errors_readout = []
    for properties in target["measure"].values():
        if properties is not None and properties.error is not None:
            errors_readout.append(properties.error)

    # coherence times, over all qubits (in microseconds)
    t1, t2 = [], []
    for q in range(backend.num_qubits):
        qp = backend.qubit_properties(q)
        if qp is not None and qp.t1 is not None:
            t1.append(qp.t1 * 1e6)
        if qp is not None and qp.t2 is not None:
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


# transpiles with several seeds and keeps the version with the fewest two-qubit gates
def transpile_best(circuit, backend, seeds=(0, 1, 2, 3, 4), optimization_level=3):
    gate_2q = get_two_qubit_gate(backend)
    best, best_count, best_seed = None, None, None

    for seed in seeds:
        pass_manager = generate_preset_pass_manager(
            backend=backend, optimization_level=optimization_level, seed_transpiler=seed)
        transpiled = pass_manager.run(circuit)
        count = transpiled.count_ops().get(gate_2q, 0)
        if best is None or count < best_count:
            best, best_count, best_seed = transpiled, count, seed

    return best, best_seed


# builds the qaoa circuit with the hamiltonian terms in original and sorted order,
# since the order changes the routing; keeps whichever transpiles to fewer two-qubit gates
def transpile_qaoa_best(H, p, params, backend, seeds=(0, 1, 2, 3, 4)):
    gate_2q = get_two_qubit_gate(backend)
    best, best_count, best_seed, best_order = None, None, None, None

    for order, hamiltonian in [("original", H), ("sorted", H.sort())]:
        circuit = build_qaoa(hamiltonian, p).assign_parameters(params)
        circuit.measure_all()
        transpiled, seed = transpile_best(circuit, backend, seeds)
        count = transpiled.count_ops().get(gate_2q, 0)
        if best is None or count < best_count:
            best, best_count, best_seed, best_order = transpiled, count, seed, order

    return best, best_seed, best_order


# esp: chance that no gate and no readout fails, from the live calibration
def estimated_success(transpiled, backend):
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


# same esp, but from a saved snapshot, so it can be recomputed later without the backend
def estimated_success_from_snapshot(transpiled, snapshot):
    readout = {q["qubit"]: q["readout_error"] for q in snapshot["qubits"]}
    sx = {q["qubit"]: q["sx_error"] for q in snapshot["qubits"]}
    two_qubit = {tuple(pair["qubits"]): pair["error"] for pair in snapshot["pairs"]}
    gate_2q = snapshot["two_qubit_gate"]

    probability = 1.0
    for instruction in transpiled.data:
        name = instruction.operation.name
        qubits = tuple(transpiled.find_bit(q).index for q in instruction.qubits)
        if name == gate_2q:
            error = two_qubit.get(qubits)
        elif name == "measure":
            error = readout.get(qubits[0])
        elif name in ("sx", "x"):
            error = sx.get(qubits[0])      # x error not in the snapshot; ≈ sx error on IBM
        else:
            error = None                   # rz (virtual), barrier, ...
        if error is not None:
            probability *= 1 - error
    return probability


# counts -> probability vector of length 2^n, indexed like Statevector.probabilities()
def counts_to_probabilities(counts, n):
    probabilities = np.zeros(2 ** n)
    shots = sum(counts.values())
    for bitstring, count in counts.items():
        probabilities[int(bitstring, 2)] = count / shots
    return probabilities


# saves the sent circuits (.qpy), the raw counts (.json) and a manifest row,
# so a job can be analysed later without the ibm account
def save_job_data(job, labels, circuits, calibration_path, folder="../data/qpu", tag=""):
    job_id = job.job_id()
    os.makedirs(os.path.join(folder, "circuits"), exist_ok=True)
    os.makedirs(os.path.join(folder, "raw"), exist_ok=True)

    # 1. the circuits exactly as they were sent
    circuits_path = os.path.join(folder, "circuits", job_id + ".qpy")
    with open(circuits_path, "wb") as f:
        qpy.dump(circuits, f)

    # 2. the raw results: counts for every circuit, by label
    result = job.result()
    counts = {label: result[i].data.meas.get_counts() for i, label in enumerate(labels)}

    raw_path = os.path.join(folder, "raw", job_id + ".json")
    with open(raw_path, "w") as f:
        json.dump({
            "job_id": job_id,
            "backend": job.backend().name,
            "created": str(job.creation_date),
            "labels": labels,
            "counts": counts,
        }, f, indent=2)

    # 3. one row in the manifest of all jobs
    manifest_path = os.path.join(folder, "manifest.csv")
    row = pd.DataFrame([{
        "job_id": job_id,
        "tag": tag,
        "backend": job.backend().name,
        "created": str(job.creation_date),
        "n_circuits": len(labels),
        "shots": sum(counts[labels[0]].values()),
        "qpu_seconds": job.usage(),
        "calibration": calibration_path,
        "circuits": circuits_path,
        "raw": raw_path,
    }])
    row.to_csv(manifest_path, mode="a", header=not os.path.exists(manifest_path), index=False)

    return raw_path