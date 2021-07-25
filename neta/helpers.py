import heapq
from collections import OrderedDict
from math import inf
from typing import Dict, Iterable, Sequence, Union

import pandas as pd


class UserHelper:
    """On initialization, loads the users.csv data into memory.
    Provides various helper methods to look up and format data about users"""

    users: pd.DataFrame

    def __init__(self):
        from constants import USERS_FILE_PATH

        self.users = pd.read_csv(USERS_FILE_PATH).set_index("id")

    def get_usernames(self, user_ids: Iterable[int]):
        return self.users.reindex(user_ids)["username"].to_list()

    def pretty_print_users(self, user_value_dict: Dict[int, float]) -> str:
        users = self.users.reindex(user_value_dict)
        users["value"] = pd.Series(user_value_dict)
        return users[["username", "value"]].to_string()


def top_n(value_dict: dict, n: int) -> Dict[str, float]:

    """Helper function to find the n highest-value keys in a dictionary.
    Runs in O(n+k) time for a dictionary with k entries."""
    if n is None or n == inf:
        return value_dict
    # Have to reformat the dict like this for heapq to cooperate.
    collection = [(value, key) for key, value in value_dict.items()]
    heapq.heapify(collection)
    top_n_items = OrderedDict()
    for nth_largest in heapq.nlargest(n, collection):
        top_n_items[nth_largest[1]] = nth_largest[0]  # Reconstruct the dict
    return top_n_items
