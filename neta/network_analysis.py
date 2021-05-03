from typing import Dict, Set
import networkx as nx
import csv
from helpers import top_n, UserHelper

EDGES_FILE_PATH = "../data/edges.csv"

GWWC_NODES = {"88534421", "363005534", "1062005076204642305", "116994659", "107336879", "30436279", "519438862",
              "1183382935", "222210727", "1183382935", "47268595", "37723353", "1110877798820777986", "181328570"}
network: nx.DiGraph


def construct_graph() -> nx.DiGraph:
    new_network = nx.DiGraph()
    with open(EDGES_FILE_PATH, 'r') as f:
        cf = csv.reader(f)
        next(cf)
        edges = [(row[0], row[1]) for row in cf]
        new_network.add_edges_from(edges)
    return new_network


def centrality() -> Dict[str, float]:
    return nx.eigenvector_centrality_numpy(network)


def out_neighbors(node: str) -> Set[str]:
    return {edge[1] for edge in network.out_edges(node)}


def get_gwwc_out_neighbors(aggregated=False):
    """
    When aggregated=False, a list of sets containing each GWWC node's out neighbors is returned. When aggregated=True,
    those sets are unioned and returned as a single set.
    :param aggregated: Determines whether the function returns a list of Set[str] or a single, aggregated Set[str]
    :return: Either a disaggregated List[Set[str]] or an aggregated Set[str].
    """
    gwwc_followed_sets = [out_neighbors(node) for node in GWWC_NODES]
    if aggregated:
        return set().union(*gwwc_followed_sets)
    return gwwc_followed_sets


def jaccard_index(n1_neighbors: Set[str], n2_neighbors: Set[str]) -> float:
    return len(n1_neighbors & n2_neighbors) / len(n1_neighbors | n2_neighbors)


def get_nodes(nonzero_out_neighbors=False, exclude_gwwc_accounts=False) -> Set[str]:
    """Returns a filtered set of nodes based on provided arguments.
    :param nonzero_out_neighbors: Excludes nodes with 0 out neighbors.
    :param exclude_gwwc_accounts: Excludes nodes included in GWWC_NODES list.
    """
    filtered_nodes = set(network.nodes)
    if nonzero_out_neighbors:
        filtered_nodes &= set(edge[0] for edge in network.edges)
    if exclude_gwwc_accounts:
        filtered_nodes -= GWWC_NODES
    return filtered_nodes


def gwwc_alignment_fast() -> Dict[str, float]:
    """Jaccard similarity between union of GWWC nodes' follows and the given node's follows"""
    gwwc_followed_set = get_gwwc_out_neighbors(aggregated=True)
    alignment_values = {}
    for node in get_nodes(nonzero_out_neighbors=True, exclude_gwwc_accounts=True):
        node_out_edges = out_neighbors(node)
        alignment_values[node] = jaccard_index(node_out_edges, gwwc_followed_set)
    return alignment_values


def gwwc_alignment_disaggregated() -> Dict[str, float]:
    """Average of Jaccard similarity for each GWWC account's follows and the given node's follows"""
    gwwc_followed_sets = get_gwwc_out_neighbors(aggregated=False)
    alignment_values = {}
    for node in get_nodes(nonzero_out_neighbors=True, exclude_gwwc_accounts=True):
        node_out_edges = out_neighbors(node)
        alignment_values[node] = \
            sum(jaccard_index(node_out_edges, followed_set) for followed_set in gwwc_followed_sets) \
            / len(gwwc_followed_sets)
    return alignment_values


if __name__ == "__main__":
    user_helper = UserHelper()
    network = construct_graph()
    most_central = top_n(centrality(), 25)
    print("Most Central Users")
    print(user_helper.pretty_print_users(most_central))
    most_aligned = top_n(gwwc_alignment_disaggregated(), 25)
    print("Most GWWC-Aligned Users")
    print(user_helper.pretty_print_users(most_aligned))
