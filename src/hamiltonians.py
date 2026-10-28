from qiskit.quantum_info import SparsePauliOp
from src.classical import cut_value, bisection_bruteforce
import numpy as np

# how close two floats must be to count as equal in the checks
TOLERANCE = 1e-9


# max-cut hamiltonian: energy = -cut, one zz term per edge
def max_cut_hamiltonian(graph):
    n = graph.number_of_nodes()
    terms = []

    for edge in graph.edges():
        i, j = edge[0], edge[1]
        terms.append(("I", [0], -0.5))
        terms.append(("ZZ", [i, j], 0.5))

    H = SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify()
    return H


# checks that the diagonal of the max-cut hamiltonian equals -cut for every bitstring
def check_max_cut_hamiltonian(graph):
    H = max_cut_hamiltonian(graph)
    diagonal = H.to_matrix(sparse=True).diagonal().real

    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"
    for i in range(2 ** n):
        bitstring = format(i, binary_format)
        cut = cut_value(graph, bitstring)

        assert abs(diagonal[i] - (-cut)) < TOLERANCE, "mismatch for bitstring " + bitstring + ": energy " + str(diagonal[i]) + ", expected " + str(-cut)


# penalty weight A = (d_max + 1) / 4, large enough that unbalanced splits never win
def generate_penalty_A(graph):
    d = dict(graph.degree())
    d_max = max(d.values())
    return (d_max + 1) / 4


# bisection hamiltonian: energy = cut + A * (sum of z)^2, the penalty couples every pair of qubits
def bisection_hamiltonian(graph, A):
    n = graph.number_of_nodes()
    terms = []

    for edge in graph.edges():
        i, j = edge[0], edge[1]
        terms.append(("I", [0], 0.5))
        terms.append(("ZZ", [i, j], -0.5))

    terms.append(("I", [0], A*n))

    for i in range(0, n-1):
        for j in range(i+1, n):
            terms.append(("ZZ", [i, j], 2*A))

    H = SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify()
    return H


# checks that the diagonal equals cut + penalty for every bitstring, unbalanced ones included
def check_bisection_hamiltonian(graph):
    A = generate_penalty_A(graph)
    H = bisection_hamiltonian(graph, A)
    diagonal = H.to_matrix(sparse=True).diagonal().real

    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"
    for i in range(2 ** n):
        bitstring = format(i, binary_format)
        spin_sum = bitstring.count("0") - bitstring.count("1")
        cut = cut_value(graph, bitstring)
        expected = cut + A * spin_sum ** 2

        assert abs(diagonal[i] - expected) < TOLERANCE, "mismatch for bitstring " + bitstring + ": energy " + str(diagonal[i]) + ", expected " + str(expected)


# true if every bitstring in the list splits the nodes half and half
def check_balanced_bitstring(bitstrings, n):
    for bitstring in bitstrings:
        zeros = bitstring.count("0")
        ones = bitstring.count("1")
        if not(zeros == n//2 or ones == n//2):
            return False

    return True


# lowest energy of the bisection hamiltonian and all bitstrings that reach it
def bisection_ground_states(graph, A):
    H_b = bisection_hamiltonian(graph, A)
    diagonal = H_b.to_matrix(sparse=True).diagonal().real
    min_energy = diagonal.min()

    ground_states = []
    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"
    for i in range(2 ** n):
        bitstring = format(i, binary_format)
        energy = diagonal[i]

        if abs(energy - min_energy) < TOLERANCE:
            ground_states.append(bitstring)

    return min_energy, ground_states


# the ground states must be exactly the optimal bisections from brute force, all balanced
def check_bisection_ground_states(graph):
    A = generate_penalty_A(graph)
    n = graph.number_of_nodes()
    min_energy, ground_states = bisection_ground_states(graph, A)
    bruteforce_cost, bruteforce_list = bisection_bruteforce(graph)

    assert abs(bruteforce_cost - min_energy) < TOLERANCE, "minimum energy " + str(min_energy) + " differs from optimum " + str(bruteforce_cost)
    assert sorted(ground_states) == sorted(bruteforce_list), "ground states differ from the optimal bisections"
    assert check_balanced_bitstring(ground_states, n), "some ground state is not balanced"


# number of zz terms, i.e. how many two-qubit interactions the circuit will need
def count_zz_terms(H):
    count = 0
    for term in H.to_sparse_list():
        if term[0] == "ZZ":
            count = count + 1
    return count