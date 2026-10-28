import random
import numpy as np

# implementare calcul taietura -------------------------
def cut_value(graph, bitstring):
    cut = 0

    for edge in graph.edges():
        i = edge[0]
        j = edge[1]
        if bitstring[-1-i] != bitstring[-1-j]:
            cut += 1

    return cut

# implementare max cut - bruteforce -------------------------
def max_cut_bruteforce(graph):
    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"

    best_value = None
    bitstring_list = []

    # generez cele 2^n combinatii
    for i in range(2 ** n):
        current_bitstring = format(i, binary_format)
        value = cut_value(graph, current_bitstring)

        if best_value is None or value > best_value:
            best_value = value
            bitstring_list = [current_bitstring]

        elif value == best_value:
            bitstring_list.append(current_bitstring)

    return best_value, bitstring_list

# implementare bisectie - bruteforce -------------------------
def bisection_bruteforce(graph):
    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"
    best_cut = None
    bitstring_list = []

    for i in range(2 ** n):
        current_bitstring = format(i, binary_format)

        # verific daca e echilibrat
        zeros = current_bitstring.count("0")
        ones = current_bitstring.count("1")

        if zeros == n//2 or ones == n//2:
            # verific daca taietura e mai buna decat ce aveam inainte
            value = cut_value(graph, current_bitstring)
            if best_cut is None or value < best_cut:
                best_cut = value
                bitstring_list = [current_bitstring]
            elif value == best_cut:
                bitstring_list.append(current_bitstring)

    return best_cut, bitstring_list

# implementare greedy pentru bisection ------------------------------------------
def random_balanced_bitstring(n, rng):
    bitstring = ["0"] * (n//2) + ["1"] * (n//2)
    rng.shuffle(bitstring)
    return "".join(bitstring)

def swap_bits(bitstring, i, j):
    bit_list = list(bitstring)
    aux = bit_list[-1-i]
    bit_list[-1-i] = bit_list[-1-j]
    bit_list[-1-j] = aux
    return "".join(bit_list)

def bitstring_to_partition(bitstring):
    machine_a = []
    machine_b = []
    reversed_bitstring = bitstring[::-1]
    for i in range(len(bitstring)):
        if (reversed_bitstring[i] == "0"):
            machine_a.append(i)
        else:
            machine_b.append(i)
    return machine_a, machine_b

def bisection_local_search(graph, start_bitstring):
    current = start_bitstring
    current_cost = cut_value(graph, current)

    while True:
        best_candidate = current
        best_candidate_cost = current_cost

        machine_a, machine_b = bitstring_to_partition(current)
        for a in machine_a:
            for b in machine_b:
                candidate = swap_bits(current, a, b)
                cost = cut_value(graph, candidate)
                if cost < best_candidate_cost:
                    best_candidate = candidate
                    best_candidate_cost = cost

        if best_candidate_cost < current_cost:
            current = best_candidate
            current_cost = best_candidate_cost
        else:
            break

    return current, current_cost


def bisection_greedy(graph, seed=42, num_restarts=20):
    # generez un bitstring random, echilibrat
    n = graph.number_of_nodes()
    rng = random.Random(seed)
    
    best_cost = None
    best_bitstring = None

    # 20 de cautari diferite
    for _ in range(num_restarts):
        # bistring-ul de start
        bitstring = random_balanced_bitstring(n, rng)

        # local search - incerc toate swap-urile posibile
        local_bitstring, local_cost = bisection_local_search(graph, bitstring)

        if best_cost is None or best_cost > local_cost:
            best_cost = local_cost
            best_bitstring = local_bitstring

    return best_cost, best_bitstring


# implementare greedy pentru max cut ------------------------------------------
def flip_bit(bitstring, pos):
    bit_list = list(bitstring)
    if bit_list[-1-pos] == "0":
        bit_list[-1-pos] = "1"
    else:
        bit_list[-1-pos] = "0"

    return "".join(bit_list)

def random_bitstring(n, rng):
    bitstring = []
    for _ in range(n):
        i = rng.choice("01")
        bitstring.append(i)

    return "".join(bitstring)

def max_cut_local_search(graph, start_bitstring):
    n = graph.number_of_nodes()
    current = start_bitstring
    current_cost = cut_value(graph, current)

    while True:
        best_candidate = current
        best_candidate_cost = current_cost

        for i in range(n):
            candidate = flip_bit(current, i)
            cost = cut_value(graph, candidate)
            if cost > best_candidate_cost:
                best_candidate = candidate
                best_candidate_cost = cost

        if best_candidate_cost > current_cost:
            current = best_candidate
            current_cost = best_candidate_cost
        else:
            break

    return current, current_cost


def max_cut_greedy(graph, num_restarts=20, seed=42):
    n = graph.number_of_nodes()
    rng = random.Random(seed)

    best_cost = None
    best_bitstring = None

    for _ in range(num_restarts):
        start = random_bitstring(n, rng)
        local_bitstring, local_cost = max_cut_local_search(graph, start)

        if best_cost is None or local_cost > best_cost:
            best_cost = local_cost
            best_bitstring = local_bitstring

    return best_cost, best_bitstring


# determin media si abaterea standard ------------------------------------------
def bisection_random_stats(graph):
    costs_list = bisection_all_costs(graph)
    return np.mean(costs_list), np.std(costs_list)

def bisection_all_costs(graph):
    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"
    costs_list = []

    # generez toate variantele
    for k in range(2 ** n):
        bitstring = format(k, binary_format)

        # verific daca e echilibrat
        zeros = bitstring.count("0")
        ones = bitstring.count("1")
        if zeros == n//2 or ones == n//2:
            costs_list.append(cut_value(graph, bitstring))
            
    return costs_list


def max_cut_random_stats(graph):
    n = graph.number_of_nodes()
    binary_format = "0" + str(n) + "b"
    costs_list = []

    # generez toate variantele
    for k in range(2 ** n):
        bitstring = format(k, binary_format)
        costs_list.append(cut_value(graph, bitstring))

    return np.mean(costs_list), np.std(costs_list)