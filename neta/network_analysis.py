from typing import Dict, Set

import networkx as nx

from neta.graph import NetworkContainer
from neta.helpers import UserHelper, top_n
from neta.recommendations import Recommendation

GWWC_NODES = frozenset({
    88534421,
    363005534,
    1062005076204642305,
    116994659,
    107336879,
    30436279,
    519438862,
    1183382935,
    222210727,
    1183382935,
    47268595,
    37723353,
    1110877798820777986,
    181328570,
})


def centrality(network) -> Dict[int, float]:
    return nx.eigenvector_centrality_numpy(network)


def out_neighbors(network, node: int) -> Set[int]:
    return {edge[1] for edge in network.edges(node)}


def get_gwwc_out_neighbors(network, aggregated=False):
    """
    When aggregated=False, a list of sets containing each GWWC node's out neighbors is returned. When aggregated=True,
    those sets are unioned and returned as a single set.
    :param aggregated: Determines whether the function returns a list of Set[int] or a single, aggregated Set[int]
    :return: Either a disaggregated List[Set[int]] or an aggregated Set[int].
    """
    gwwc_followed_sets = [out_neighbors(network, node) for node in GWWC_NODES]
    if aggregated:
        return set().union(*gwwc_followed_sets)
    return gwwc_followed_sets


def jaccard_index(n1_neighbors: Set[int], n2_neighbors: Set[int]) -> float:
    return len(n1_neighbors & n2_neighbors) / len(n1_neighbors | n2_neighbors)


def get_nodes(
    network, nonzero_out_neighbors=False, exclude_gwwc_accounts=False
) -> Set[int]:
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


def node_alignment(network, node_id: int) -> Dict[int, float]:
    alignment_values = {}
    given_node_neighbors = out_neighbors(network, node_id)
    for other_node in get_nodes(network, nonzero_out_neighbors=True):
        if other_node != node_id:
            try:
                alignment_values[other_node] = jaccard_index(
                    out_neighbors(network, other_node), given_node_neighbors
                )
            except:
                print("failure")
    return alignment_values


def gwwc_alignment_fast(network) -> Dict[int, float]:
    """Jaccard similarity between union of GWWC nodes' follows and the given node's follows"""
    gwwc_followed_set = get_gwwc_out_neighbors(network, aggregated=True)
    alignment_values = {}
    for node in get_nodes(
        network, nonzero_out_neighbors=True, exclude_gwwc_accounts=True
    ):
        node_out_edges = out_neighbors(network, node)
        alignment_values[node] = jaccard_index(node_out_edges, gwwc_followed_set)
    return alignment_values


def gwwc_alignment_disaggregated(network) -> Dict[int, float]:
    """Average of Jaccard similarity for each GWWC account's follows and the given node's follows"""
    gwwc_followed_sets = get_gwwc_out_neighbors(network, aggregated=False)
    alignment_values = {}
    for node in get_nodes(
        network, nonzero_out_neighbors=True, exclude_gwwc_accounts=True
    ):
        node_out_edges = out_neighbors(network, node)
        alignment_values[node] = sum(
            jaccard_index(node_out_edges, followed_set)
            for followed_set in gwwc_followed_sets
        ) / len(gwwc_followed_sets)
    return alignment_values


def normalize_dict(value_dict: Dict[int, float]) -> Dict[int, float]:
    factor = 1.0 / sum(value_dict.values())
    return {key: val * factor for key, val in value_dict.items()}


def connector_nodes(network, other_node: int) -> Dict[int, float]:
    gwwc_alignments = normalize_dict(gwwc_alignment_fast(network))
    other_node_alignments = normalize_dict(node_alignment(network, other_node))
    overlapping_keys = set(gwwc_alignments.keys()) & set(other_node_alignments.keys())
    alignment_sums = {}
    for key in overlapping_keys:
        alignment_sums[key] = gwwc_alignments[key] + other_node_alignments[key]
    return alignment_sums


if __name__ == "__main__":
    user_helper = UserHelper()
    network_container = NetworkContainer.get_network(
        directed=False, enable_caching=False
    )
    network = network_container.network
    recommendation_engine = Recommendation(network_container)
    most_central = top_n(centrality(network), 25)
    # print("Most Central Users")
    # print(user_helper.pretty_print(most_central))
    most_aligned = recommendation_engine.recommendations(GWWC_NODES, 100)
    # most_aligned = top_n(gwwc_alignment_fast(network), 25)
    print("Most GWWC-Aligned Users")
    print(user_helper.pretty_print(most_aligned))
    # comparison_acct = 14717311  # @elonmusk
    # conn_nodes = top_n(connector_nodes(network, comparison_acct), 25)
    # print(user_helper.pretty_print(conn_nodes))
