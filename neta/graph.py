import os
import pickle
from collections import defaultdict
from typing import Dict, NamedTuple

import networkx as nx
import numpy as np
import pandas as pd

from neta.constants import EDGE_CSV_PATH, NETWORK_CACHE_PATH


class NodeMetadata(NamedTuple):
    start: int
    end: int
    length: int


class NetworkEdgeList:
    """
    An alternative representation of a network that is optimized for random sampling of
    neighbors.
    """

    edge_list: np.array
    node_metadata: Dict[int, NodeMetadata]

    def __init__(self, edges, directed=True, version="following"):
        source = "follower" if version == "following" else "followed"
        target = "followed" if version == "following" else "follower"
        neighbor_dict = (
            edges.groupby(source)
            .apply(lambda x: list(x[target]))
            .to_dict(into=defaultdict(list))
        )
        n = len(edges)
        if not directed:
            edges.apply(lambda x: neighbor_dict[x[target]].append(x[source]), axis=1)
            n *= 2

        self.edge_list = np.empty(n, dtype="int64")
        self.node_metadata = {}

        prev_index = 0
        for node, neighbors in neighbor_dict.items():
            np_neighbors = np.array(neighbors, dtype="int64")
            start_idx = prev_index
            end_idx = start_idx + len(neighbors)
            self.node_metadata[node] = NodeMetadata(
                start=start_idx, end=end_idx, length=len(neighbors)
            )
            self.edge_list[start_idx:end_idx] = np_neighbors
            prev_index = end_idx


class NetworkContainer:
    network: nx.Graph
    network_edge_list: NetworkEdgeList
    version: str

    def __init__(self, directed=False, version="following", edges=None):
        if edges is None:
            edges = pd.read_csv(EDGE_CSV_PATH)
        self.network = self.construct_network(edges, directed, version)
        self.network_edge_list = NetworkEdgeList(edges, directed, version)
        self.version = version

    def cache(self):
        print("Caching network.")
        with open(NETWORK_CACHE_PATH.format(self.version), "wb") as cache_file:
            pickle.dump(self, cache_file)

    @staticmethod
    def get_network(
        enable_caching=True,
        directed=True,
        version="following",
        edges=None,
        rebuild_nel=False,
    ):

        if not enable_caching:
            return NetworkContainer(directed, version, edges)
        if os.path.exists(NETWORK_CACHE_PATH.format(version)):
            try:
                with open(NETWORK_CACHE_PATH.format(version), "rb") as cache_file:
                    print("Loading network from cache.")
                    network_container = pickle.load(cache_file)
                    if directed and not network_container.network.is_directed():
                        network_container.network = (
                            network_container.network.to_directed()
                        )
                    elif not directed and network_container.network.is_directed():
                        network_container.network = (
                            network_container.network.to_undirected()
                        )
                    # Rebuilding the NEL should be done only if it was originally
                    # written as directed, and is then used for the recommender method
                    if rebuild_nel:
                        network_container.network_edge_list = NetworkEdgeList(
                            edges, directed, version
                        )
                    return network_container
            except BaseException as err:
                print("Loading network from cache file failed with error:", err)
                # Create a new network if fetching from cache fails
                return NetworkContainer(directed, version, edges)
        else:
            # Otherwise, construct a new network and cache it.
            new_network = NetworkContainer(directed, version, edges)
            new_network.cache()
            return new_network

    @staticmethod
    def construct_network(edges, directed=True, version="following"):
        return nx.from_pandas_edgelist(
            edges,
            "follower" if version == "following" else "followed",
            "followed" if version == "following" else "follower",
            create_using=nx.DiGraph if directed else nx.Graph,
        )
