import heapq
from collections import OrderedDict


def top_n(value_dict: dict, n: int):
    """Helper function to find the n highest-value keys in a dictionary. Runs in O("""
    # Have to reformat the dict like this for heapq to cooperate.
    collection = [(value, key) for key, value in value_dict.items()]
    heapq.heapify(collection)
    top_n_items = OrderedDict()
    for nth_largest in heapq.nlargest(n, collection):
        top_n_items[nth_largest[1]] = nth_largest[0]  # Reconstruct the dict
    return top_n_items