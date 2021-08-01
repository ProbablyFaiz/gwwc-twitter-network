import heapq
from collections import OrderedDict
from math import inf
from typing import Dict

import pandas as pd


class UserHelper:
    """On initialization, loads the users.csv data into memory.
    Provides various helper methods to look up and format data about users"""

    users: pd.DataFrame

    def __init__(self, users=None):
        """Initialize user helper.

        :param users: (optional) dataframe containing user data
        """
        from neta.constants import USERS_FILE_PATH

        if users is None:
            users = pd.read_csv(USERS_FILE_PATH)
        self.users = users.set_index("id")

    def users_with_values(self, user_value_dict: Dict[int, float]):
        users = self.users.reindex(user_value_dict)
        users["value"] = pd.Series(user_value_dict)
        return users

    def get_username(self, id):
        return self.users.loc[id, "username"]

    def pretty_print(self, user_value_dict: Dict[int, float]) -> str:
        users = self.users_with_values(user_value_dict)
        return users[["username", "value"]].to_string()


def top_n(value_dict: dict, n: int) -> Dict[int, float]:

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
