import networkx as nx
import json
from src.paths import DATA

# instance settings: sizes, seed, grid shape for each n, edge probability for random graphs
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


# ring: every node linked to the next one, the last back to the first
def make_ring(n):
    return nx.cycle_graph(n)


# rows x cols grid, with the (i, j) node labels turned into 0, 1, 2, ...
def make_grid(rows, cols):
    grid = nx.grid_2d_graph(rows, cols)
    return nx.convert_node_labels_to_integers(grid)


# random graph where every node has exactly 3 neighbours
def make_regular3(n, seed):
    return nx.random_regular_graph(3, n, seed=seed)


# erdos-renyi graph with edge probability p; bumps the seed until the graph is connected
def make_random(n, p, seed):
    current_seed = seed
    while True:
        graph = nx.erdos_renyi_graph(n, p, seed=current_seed)
        if nx.is_connected(graph):
            return graph, current_seed
        current_seed = current_seed + 1


# every pair of nodes is connected
def make_complete(n):
    return nx.complete_graph(n)


# packs a graph into a json-friendly dict: name, type, size, seed, edge list
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


# rebuilds the networkx graph from a saved instance
def json_to_graph(instance):
    graph = nx.Graph()
    graph.add_nodes_from(range(instance["n"]))
    for edge in instance["edges"]:
        graph.add_edge(edge[0], edge[1])
    return graph


# looks up an instance by name, e.g. "ring_12"
def find_instance(instances, name):
    for instance in instances:
        if instance["name"] == name:
            return instance
    return None


# all 25 instances: 5 graph types x 5 sizes
def build():
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


# writes the instances to json, one instance per line so the file stays readable
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


# reads the instances back from the json file
def load_instances(path):
    file = open(path, "r")
    content = json.load(file)
    file.close()
    return content


# python -m src.graphs regenerates data/instances.json
if __name__ == "__main__":
    instances = build()
    save_instances(instances, DATA / "instances.json")