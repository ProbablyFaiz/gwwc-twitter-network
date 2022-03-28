from collections import defaultdict

from math import inf
from typing import List, Iterable, Dict

from neta.graph import NetworkEdgeList, NetworkContainer
from neta.helpers import UserHelper

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
    shortest_path_node_is_in: Dict[int, int] = defaultdict(lambda: inf)
    # Breadth-first to avoid doing unnecessary exponential searches
    for path_length in range(1, max_path_length + 1):
        for source_node in source_nodes:
            for path_candidate in get_paths_of_length(
                graph, target_node, source_node, path_length
            ):
                should_keep = True
                for node in path_candidate[:-1]:
                    if shortest_path_node_is_in[node] < path_length:
                        should_keep = False
                        break
                    shortest_path_node_is_in[node] = min(
                        shortest_path_node_is_in[node], path_length
                    )
                if should_keep:
                    paths.append(path_candidate[::-1])
            # print(f"Paths found for {source_node} with max path length {path_length}: {paths_for_source}")
        if len(paths) >= n:
            break
    return paths[:n]


def get_paths_of_length(
    graph: NetworkEdgeList, current_node: int, target_node: int, length: int
) -> List[Path]:
    if length == 0:
        if current_node == target_node:
            return [[current_node]]
        return []
    try:
        paths = []
        node_meta = graph.node_metadata[current_node]
        neighbors = graph.edge_list[node_meta.start : node_meta.end]
        for neighbor in neighbors:
            paths.extend(
                [
                    [current_node] + path
                    for path in get_paths_of_length(
                        graph, neighbor, target_node, length - 1
                    )
                ]
            )
    except KeyError:
        return []
    return paths


def pretty_connectors(
    network: NetworkContainer,
    user_helper: UserHelper,
    target_username: str,
    n=5,
    path_length=3,
) -> str:
    """
    Returns a string with the top 5 connectors for the given user.
    """
    graph = network.network_edge_list
    # Get the top 5 connectors for the target user
    top_connectors = get_connector_paths(
        graph,
        [user_helper.get_id("givingwhatwecan")],
        user_helper.get_id(target_username),
        n=n,
        max_path_length=path_length,
    )
    return "\n".join(
        " -> ".join(user_helper.get_username(node) for node in path)
        for path in top_connectors
    )


elon_musk_acct = 18622869  # For testing

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
        print(f"{' IS FOLLOWED BY '.join(usernames)}")
    # print(shortest_paths)
