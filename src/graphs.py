import networkx as nx
import json

SIZES = [6, 8, 10, 12, 14]
BASE_SEED = 42
GRID_SIZES = {
    6: (2, 3),
    8: (2, 4),
    10: (2, 5),
    12: (3, 4),
    14: (2, 7)
}
PROBABILITY = 0.4

# functiile generatoare de grafuri -------------------------------------------------
# graf inel
def make_ring(n):
    return nx.cycle_graph(n)

# graf de tip grid
# fiecare nod are pozitie (i,j) => la final trebuie indexate ca 0,1,2,3,...
def make_grid(rows, cols):
    grid = nx.grid_2d_graph(rows, cols)
    return nx.convert_node_labels_to_integers(grid)

# graf in care fiecare nod are exact 3 vecini
def make_regular3(n, seed):
    return nx.random_regular_graph(3, n, seed=seed)

# graf random - fiecare pereche de noduri e conectata cu probabilitatea p
# daca graful nu e conectat - reincerc
def make_random(n, p, seed):
    current_seed = seed
    while True:
        graph = nx.erdos_renyi_graph(n, p, seed=current_seed)
        if nx.is_connected(graph):
            return graph, current_seed
        current_seed = current_seed + 1

# graf complet
def make_complete(n):
    return nx.complete_graph(n)

# traduc graful in text JSON -------------------------------------------------
def graph_to_json(name, graph_type, n, seed, graph):
    edges = []
    for edge in graph.edges():
        edges.append([edge[0], edge[1]])
    instance = {
        "name": name,
        "graph_type": graph_type,
        "n": n,
        "seed": seed,
        "edges": edges
    }
    return instance

# formez graful din input JSON
def json_to_graph(instance):
    graph = nx.Graph()
    graph.add_nodes_from(range(instance["n"]))
    for edge in instance["edges"]:
        graph.add_edge(edge[0], edge[1])
    return graph

def find_instance(instances, name):
    for instance in instances:
        if instance["name"] == name:
            return instance
    return None

# construiesc instantele -------------------------------------------------
def build():
    # toate instantele pe care o sa le adaug in JSON
    instances = []

    for n in SIZES:
        graph = make_ring(n)
        instances.append(graph_to_json("ring_" + str(n), "ring", n, None, graph))

        graph = make_grid(GRID_SIZES[n][0], GRID_SIZES[n][1])
        instances.append(graph_to_json("grid_" + str(n), "grid", n, None, graph))

        graph = make_regular3(n, BASE_SEED)
        instances.append(graph_to_json("regular3_" + str(n), "regular3", n, BASE_SEED, graph))

        graph, used_seed = make_random(n, PROBABILITY, BASE_SEED)
        instances.append(graph_to_json("random_" + str(n), "random", n, used_seed, graph))

        graph = make_complete(n)
        instances.append(graph_to_json("complete_" + str(n), "complete", n, None, graph))

    return instances

# prelucrez fisierul JSON -------------------------------------------------
def save_instances(instances, path):
    file = open(path, "w")
    file.write("[\n")

    for k in range(len(instances)):
        line = json.dumps(instances[k])
        if k < len(instances) - 1:
            line = line + ","
        file.write("  " + line + "\n")
        
    file.write("]\n")
    file.close()

def load_instances(path):
    file = open(path, "r")
    content = json.load(file)
    file.close()
    return content

# apelez functia main -------------------------------------------------
if __name__ == "__main__":
    instances = build()
    save_instances(instances, "../data/instances.json")
