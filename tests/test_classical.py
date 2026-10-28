import networkx as nx

from src.classical import (cut_value, max_cut_bruteforce, bisection_bruteforce,
                           max_cut_greedy, bisection_greedy, bisection_random_stats)
from src.graphs import build, json_to_graph


# bit i is read from the right: "001" puts node 0 alone on the other machine
def test_cut_value_triangle():
    triangle = nx.Graph([(0, 1), (0, 2), (1, 2)])
    assert cut_value(triangle, "000") == 0
    assert cut_value(triangle, "111") == 0
    assert cut_value(triangle, "001") == 2


# an asymmetric graph catches a reversed bit order, a triangle cannot
def test_cut_value_bit_order():
    one_edge = nx.Graph([(0, 1)])
    one_edge.add_node(2)
    assert cut_value(one_edge, "001") == 1     # node 0 -> 1, node 1 -> 0: edge cut
    assert cut_value(one_edge, "100") == 0     # only node 2 moves: edge not cut


# ring_6: max-cut alternates the machines (cut 6), bisection cuts the ring in two arcs (cut 2)
def test_bruteforce_ring6():
    ring = nx.cycle_graph(6)
    optimum, bitstrings = max_cut_bruteforce(ring)
    assert optimum == 6
    assert sorted(bitstrings) == ["010101", "101010"]

    optimum, bitstrings = bisection_bruteforce(ring)
    assert optimum == 2
    assert all(b.count("0") == 3 for b in bitstrings)


# every optimal solution comes with its complement, so the count is even
def test_optima_come_in_pairs():
    graph = json_to_graph([i for i in build() if i["name"] == "random_8"][0])
    _, bitstrings = bisection_bruteforce(graph)
    flipped = {b.translate(str.maketrans("01", "10")) for b in bitstrings}
    assert flipped == set(bitstrings)


# greedy reaches the exact optimum on the small instances
def test_greedy_matches_bruteforce():
    for instance in build():
        if instance["n"] > 8:
            continue
        graph = json_to_graph(instance)
        assert max_cut_greedy(graph)[0] == max_cut_bruteforce(graph)[0], instance["name"]
        assert bisection_greedy(graph)[0] == bisection_bruteforce(graph)[0], instance["name"]


# on a complete graph every bisection cuts (n/2)^2 edges, so the spread is zero
def test_random_stats_complete_graph():
    mean, std = bisection_random_stats(nx.complete_graph(6))
    assert mean == 9
    assert std == 0
