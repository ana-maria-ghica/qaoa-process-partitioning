from qiskit.quantum_info import SparsePauliOp
from src.classical import cut_value, bisection_bruteforce
import numpy as np

TOLERANCE = 1e-9

# definesc hamiltonianul pentru max cut
def max_cut_hamiltonian(graph):
    n = graph.number_of_nodes()
    terms = []

    for edge in graph.edges():
        i, j = edge[0], edge[1]
        terms.append(("I", [0], -0.5))
        terms.append(("ZZ", [i, j], 0.5))

    H = SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify()
    return H

# determin matricea diagonala pt hamiltonian + validez valorile
def check_max_cut_hamiltonian(graph):
    H = max_cut_hamiltonian(graph)
    diagonal = H.to_matrix(sparse=True).diagonal().real

    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"
    for i in range(2 ** n):
        bitstring = format(i, binary_format)
        cut = cut_value(graph, bitstring)

        assert abs(diagonal[i] - (-cut)) < TOLERANCE, "mismatch for bitstring " + bitstring + ": energy " + str(diagonal[i]) + ", expected " + str(-cut)


# determin penalizarea A
def generate_penalty_A(graph):
    d = dict(graph.degree())
    d_max = max(d.values())
    return (d_max + 1) / 4

# definesc hamiltonianul pentru bisection
def bisection_hamiltonian(graph, A):
    n = graph.number_of_nodes()
    terms = []

    # for-ul peste toate muchiile
    for edge in graph.edges():
        i, j = edge[0], edge[1]
        terms.append(("I", [0], 0.5))
        terms.append(("ZZ", [i, j], -0.5))

    # penalizarea
    terms.append(("I", [0], A*n))

    # for-ul peste perechi (termenii ZiZj ai penalizarii)
    for i in range(0, n-1):
        for j in range(i+1, n):
            terms.append(("ZZ", [i, j], 2*A))

    H = SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify()
    return H

# determin matricea diagonala pt hamiltonian + validez valorile
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

        assert abs(diagonal[i] - expected) < TOLERANCE, "mismatch for bitstring " + bitstring + ": energy " + str(diagonal[i]) + ", expected " + str(cut)

def check_balanced_bitstring(bitstrings, n):
    for bitstring in bitstrings:
        zeros = bitstring.count("0")
        ones = bitstring.count("1")
        if not(zeros == n//2 or ones == n//2):
            return False

    return True
        

def bisection_ground_states(graph, A):
    # A = generate_penalty_A(graph)
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


def check_bisection_ground_states(graph):
    min_energy, ground_states = bisection_ground_states(graph)
    bruteforce_cost, bruteforce_list = bisection_bruteforce(graph)

    assert abs(bruteforce_cost - min_energy) < TOLERANCE, "minimum energy " + str(min_energy) + " differs from optimum " + str(bruteforce_cost)
    assert sorted(ground_states) == sorted(bruteforce_list), "ground states differ from the optimal bisections"
    assert check_balanced_bitstring(ground_states, n), "some ground state is not balanced"



# numar termenii ZZ din hamiltonian
def count_zz_terms(H):
    count = 0
    for term in H.to_sparse_list():
        if term[0] == "ZZ":
            count = count + 1
    return count