import numpy as np
from qiskit import QuantumCircuit

from src.hardware import counts_to_probabilities, estimated_success_from_snapshot


# counts -> probabilities: sums to 1, bitstring read as a binary number
def test_counts_to_probabilities():
    probabilities = counts_to_probabilities({"01": 3, "10": 1}, 2)
    assert np.isclose(probabilities.sum(), 1)
    assert probabilities[1] == 0.75
    assert probabilities[2] == 0.25


# esp of one cz and two measurements = product of the three success probabilities
def test_esp_from_snapshot():
    circuit = QuantumCircuit(2, 2)
    circuit.cz(0, 1)
    circuit.measure([0, 1], [0, 1])
    snapshot = {
        "two_qubit_gate": "cz",
        "qubits": [{"qubit": 0, "readout_error": 0.01, "sx_error": 0.001},
                   {"qubit": 1, "readout_error": 0.02, "sx_error": 0.001}],
        "pairs": [{"qubits": [0, 1], "error": 0.005}],
    }
    expected = (1 - 0.005) * (1 - 0.01) * (1 - 0.02)
    assert np.isclose(estimated_success_from_snapshot(circuit, snapshot), expected)
