import networkx as nx

from src.graphs import build, json_to_graph
from src.hamiltonians import (check_max_cut_hamiltonian, check_bisection_hamiltonian,
                              check_bisection_ground_states, bisection_ground_states,
                              bisection_hamiltonian, max_cut_hamiltonian,
                              generate_penalty_A, check_balanced_bitstring, count_zz_terms)

GRAPHS = [json_to_graph(i) for i in build() if i["name"] in ("ring_6", "grid_8", "random_8", "regular3_10")]


# the diagonal of both hamiltonians must equal the classical cost on every bitstring
def test_hamiltonians_match_classical_cost():
    for graph in GRAPHS:
        check_max_cut_hamiltonian(graph)
        check_bisection_hamiltonian(graph)


# the lowest-energy states of the bisection hamiltonian are exactly the optimal balanced splits
def test_bisection_ground_states():
    for graph in GRAPHS:
        check_bisection_ground_states(graph)
        _, ground_states = bisection_ground_states(graph, generate_penalty_A(graph))
        assert check_balanced_bitstring(ground_states, graph.number_of_nodes())


# max-cut has one zz term per edge, bisection one per pair of qubits
def test_zz_term_counts():
    ring = nx.cycle_graph(8)
    assert count_zz_terms(max_cut_hamiltonian(ring)) == 8
    assert count_zz_terms(bisection_hamiltonian(ring, generate_penalty_A(ring))) == 8 * 7 // 2
