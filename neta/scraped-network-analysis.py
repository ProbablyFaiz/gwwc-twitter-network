import networkx as nx
import csv
import heapq

EDGES_FILE_PATH = "../data/edges.csv"

GWWC_NODES = map(str, [88534421, 363005534, 1062005076204642305, 116994659, 107336879, 519438862, 1183382935, 47268595,
                       37723353, 1110877798820777986, 181328570])


def construct_graph():
    follower_graph = nx.DiGraph()
    with open(EDGES_FILE_PATH, 'r') as f:
        cf = csv.reader(f)
        next(cf)
        edges = [(row[0], row[1]) for row in cf]
        follower_graph.add_edges_from(edges)
    return follower_graph


def top_n(collection, n):
    heapq.heapify(collection)
    top_n_items = []
    while len(top_n_items) < n:
        nth_lowest = heapq.heappop(collection)
        top_n_items.append(nth_lowest)
    return top_n_items


graph = construct_graph()
centrality = [(-cent, node) for node, cent in nx.eigenvector_centrality_numpy(graph).items()]
most_central = top_n(centrality, 20)
print(most_central)

