import csv
from collections import defaultdict
from typing import NamedTuple, Dict
import numpy as np
from constants import EDGE_CSV_PATH


class NodeMetadata(NamedTuple):
    start: int
    end: int
    length: int


class NetworkEdgeList:
    """
    An alternative representation of a network that is optimized for random sampling of neighbors
    """
    edge_list: np.array
    node_metadata: Dict[int, NodeMetadata]

    def __init__(self, ):
        edge_list_size = 0
        neighbor_dict = defaultdict(list)
        with open(EDGE_CSV_PATH, 'r') as cf:
            csv_reader = csv.reader(cf)
            next(csv_reader)
            for row in csv_reader:
                neighbor_dict[row[0]].append(row[1])
                neighbor_dict[row[1]].append(row[0])
                edge_list_size += 2

        self.edge_list = np.empty(edge_list_size, dtype='int32')
        self.node_metadata = {}

        prev_index = 0
        for node, neighbors in neighbor_dict.items():
            np_neighbors = np.array(neighbors, dtype='int32')
            start_idx = prev_index
            end_idx = start_idx + len(neighbors)
            self.node_metadata[node] = NodeMetadata(start=start_idx, end=end_idx,
                                                    length=len(neighbors))
            self.edge_list[start_idx:end_idx] = np_neighbors
            prev_index = end_idx
