import networkx as nx
import csv
import heapq
from collections import OrderedDict

EDGES_FILE_PATH = "../data/edges.csv"

GWWC_NODES = map(str, [88534421, 363005534, 1062005076204642305, 116994659, 107336879, 519438862, 1183382935, 47268595,
                       37723353, 1110877798820777986, 181328570])
network: nx.DiGraph


def construct_graph():
    new_network = nx.DiGraph()
    with open(EDGES_FILE_PATH, 'r') as f:
        cf = csv.reader(f)
        next(cf)
        edges = [(row[0], row[1]) for row in cf]
        new_network.add_edges_from(edges)
    return new_network


def top_n(value_dict: dict, n: int):
    """Helper function to find the n highest-value keys in a dictionary. Runs in O("""
    # Have to reformat the dict like this for heapq to cooperate.
    collection = [(value, key) for key, value in value_dict.items()]
    heapq.heapify(collection)
    top_n_items = OrderedDict()
    for nth_largest in heapq.nlargest(n, collection):
        top_n_items[nth_largest[1]] = nth_largest[0]  # Reconstruct the dict
    return top_n_items


def centrality():
    return nx.eigenvector_centrality_numpy(network)


def out_neighbors(node):
    return {edge[1] for edge in network.out_edges(node)}


def get_gwwc_combined_out_neighbors():
    gwwc_followed_sets = [out_neighbors(node) for node in GWWC_NODES]
    return set().union(*gwwc_followed_sets)


def jaccard_index(n1_neighbors, n2_neighbors):
    return len(n1_neighbors & n2_neighbors) / len(n1_neighbors | n2_neighbors)


def gwwc_alignment_fast(gwwc_followed_set):
    """Jaccard similarity between union of GWWC nodes' follows and the given node's follows"""
    alignment_values = {}
    for node in network.nodes:
        node_out_edges = out_neighbors(node)
        alignment_values[node] = jaccard_index(node_out_edges, gwwc_followed_set)
    return alignment_values


if __name__ == "__main__":
    network = construct_graph()
    gwwc_out_neighbors = get_gwwc_combined_out_neighbors()
    most_central = top_n(centrality(), 20)
    print(most_central)
    most_aligned = top_n(gwwc_alignment_fast(gwwc_out_neighbors), 50)
    print(most_aligned)
