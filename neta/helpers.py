import heapq
from collections import OrderedDict
from typing import TypedDict, Dict, Iterable, List
import csv

USERS_FILE_PATH = "../data/users.csv"


class User(TypedDict):
    id: str
    username: str
    name: str
    verified: bool
    followers_count: int
    following_count: int


class UserHelper:
    """On initialization, loads the users.csv data into memory.
    Provides various helper methods to look up and format data about users"""
    users: Dict[str, User]

    def __init__(self):
        with open(USERS_FILE_PATH, 'r') as f:
            cf = csv.reader(f)
            next(cf)
            self.users = {str(row[0]): {
                "id": str(row[0]),
                "username": str(row[1]),
                "name": str(row[3]),
                "verified": row[6] == "t",
                "followers_count": int(row[7]),
                "following_count": int(row[8]),
            } for row in cf}
        pass

    def get_usernames(self, user_ids: Iterable[str]) -> List[str]:
        usernames = []
        for user_id in user_ids:
            if user_id in self.users:
                usernames.append(self.get_user(user_id)["username"])
            else:
                usernames.append(None)
        return usernames

    def get_user(self, user_id: str) -> User:
        return self.users.get(user_id)

    def pretty_print_users(self, user_value_dict: Dict[str, float]) -> str:
        output = ""
        for user_id, value in user_value_dict.items():
            user = self.get_user(user_id)
            output += f"{user['username']}: {value}\n"
        return output


def top_n(value_dict: dict, n: int) -> Dict[str, float]:
    """Helper function to find the n highest-value keys in a dictionary. Runs in O("""
    # Have to reformat the dict like this for heapq to cooperate.
    collection = [(value, key) for key, value in value_dict.items()]
    heapq.heapify(collection)
    top_n_items = OrderedDict()
    for nth_largest in heapq.nlargest(n, collection):
        top_n_items[nth_largest[1]] = nth_largest[0]  # Reconstruct the dict
    return top_n_items
