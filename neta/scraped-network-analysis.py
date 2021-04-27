import networkx as nx
import csv

EDGES_FILE_PATH = "../data/edges.csv"

GWWC_NODES = [88534421, 363005534, 1062005076204642305, 116994659, 107336879, 519438862, 1183382935, 47268595, 37723353,
              1110877798820777986, 181328570]


def construct_graph():
    follower_graph = nx.DiGraph()
    with open(EDGES_FILE_PATH, 'r') as f:
        cf = csv.reader(f)
        next(cf)
        edges = [(row[0], row[1]) for row in cf]
        follower_graph.add_edges_from(edges)
    return follower_graph


graph = construct_graph()
print(nx.number_of_edges(graph))
