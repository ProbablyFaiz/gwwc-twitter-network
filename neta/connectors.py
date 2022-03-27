from typing import List, Iterable

from neta.graph import NetworkEdgeList, NetworkContainer
from neta.helpers import UserHelper
from network_analysis import GWWC_NODES

MAX_PATH_LENGTH = 3

Path = List[int]


def get_connector_paths(
    graph: NetworkEdgeList,
    source_nodes: Iterable[int],
    target_node: int,
    n=5,
    max_path_length=MAX_PATH_LENGTH,
) -> List[Path]:
    """
    Returns the shortest n paths from any of the source_nodes to target_node.
    """
    paths = []
    # Breadth-first to avoid doing unnecessary exponential searches
    for path_length in range(1, max_path_length + 1):
        for source_node in source_nodes:
            paths_for_source = get_paths_of_length(graph, target_node, source_node, path_length)
            paths.extend(paths_for_source)
            # print(f"Paths found for {source_node} with max path length {path_length}: {paths_for_source}")
        if len(paths) >= n:
            break
    paths.sort(key=lambda p: len(p))
    return paths[:n]


def get_paths_of_length(graph: NetworkEdgeList, current_node: int, target_node: int, length: int) -> List[Path]:
    if length == 0:
        if current_node == target_node:
            return [[current_node]]
        return []
    try:
        paths = []
        node_meta = graph.node_metadata[current_node]
        neighbors = graph.edge_list[node_meta.start : node_meta.end]
        for neighbor in neighbors:
            paths.extend([[current_node] + path for path in get_paths_of_length(graph, neighbor, target_node, length - 1)])
    except KeyError:
        return []
    return paths


elon_musk_acct = 44196397  # For testing

if __name__ == "__main__":
    graph = NetworkContainer.get_network()
    print("Graph loaded...")
    user_helper = UserHelper()
    print("User helper loaded...")
    shortest_paths = get_connector_paths(
        graph.network_edge_list, [88534421], target_node=elon_musk_acct, n=5
    )
    for path in shortest_paths:
        usernames = [user_helper.get_username(path_uid) for path_uid in path]
        print(f"{' FOLLOWS '.join(usernames)}")
    # print(shortest_paths)
