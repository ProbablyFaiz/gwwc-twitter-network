import csv
import pickle
import os
import networkx as nx

from constants import NETWORK_CACHE_PATH, EDGE_CSV_PATH
from graph.network_edge_list import NetworkEdgeList


class CitationNetwork:
    network: nx.Graph
    network_edge_list: NetworkEdgeList

    def __init__(self, directed=False):
        self.network = self.construct_network(directed)
        self.network_edge_list = NetworkEdgeList()

    @staticmethod
    def get_citation_network(enable_caching=True):
        cache_file_path = NETWORK_CACHE_PATH
        if not enable_caching:
            return CitationNetwork()
        if os.path.exists(cache_file_path):
            try:
                with open(cache_file_path, 'rb') as cache_file:
                    return pickle.load(cache_file)
            except BaseException as err:
                print("Loading citation network from cache file failed with error:", err)
                return CitationNetwork()  # Create a new network if fetching from cache fails
        else:  # Otherwise, construct a new network and cache it.
            new_network = CitationNetwork()
            try:
                with open(cache_file_path, 'wb') as cache_file:
                    pickle.dump(new_network, cache_file)
            except BaseException as err:
                print("Saving citation network to cache file failed with error:", err)
            return new_network

    @staticmethod
    def construct_network(directed=False):
        if directed:
            citation_network = nx.DiGraph()
        else:
            citation_network = nx.Graph()
        with open(EDGE_CSV_PATH, 'r') as cf:
            csv_reader = csv.reader(cf)
            next(csv_reader)
            citations = list(csv_reader)
            citation_network.add_edges_from(citations)
        return citation_network
