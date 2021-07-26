import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import typer

from neta import scrape
from neta.constants import EDGE_CSV_PATH, USERS_FILE_PATH
from neta.graph import NetworkContainer
from neta.helpers import UserHelper, top_n
from neta.network_analysis import (
    GWWC_NODES,
    connector_nodes,
    gwwc_alignment_fast,
)
from neta.recommendations import Recommendation

app = typer.Typer()


def analyze_user(
    lookup: str = typer.Argument(..., help="Twitter ID or handle to analyze"),
    method: str = typer.Option(
        "following",
        help="Analyze 'following' or 'followers' (needs to match constants.py)",
    ),
    undirected: bool = typer.Option(
        False, "--undirected", help="Use an undirected graph."
    ),
    n: int = typer.Option(25, help="No. of results to return, ie. 25 recommendations"),
    use_recommender: bool = typer.Option(
        False, "--use-recommender", help="Pass to use recommender method."
    ),
    logfile: str = typer.Option("./analyze.log", help="Directory to save logs in."),
):
    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)-5s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)-5s %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    users = pd.read_csv(USERS_FILE_PATH)
    edges = pd.read_csv(EDGE_CSV_PATH)
    # This won't be updated with new users, which should be fine (new users shouldn't
    # show up in results!)
    user_helper = UserHelper(users)
    logging.info("Loaded users + edges, loading network.")
    network_container = NetworkContainer.get_network(
        directed=not undirected, edges=edges
    )

    user = lookup_user(lookup, id=True if lookup.isnumeric() else False)
    user["id"] = int(user["id"])
    # Define source/target and add to csvs if not in graph already
    source = "follower" if method == "following" else "followed"
    target = "followed" if method == "following" else "follower"

    if user["id"] in edges[source]:
        logging.info(f"User {user} already in dataset - starting analysis.")
    else:
        if user["id"] not in users["id"].to_numpy():
            append_user(user)

        n_follows = user["public_metrics"][
            f"follow{'ing' if method=='following' else 'ers'}_count"
        ]

        logging.info(
            f"{user['username']} has {n_follows} {method}. "
            f"They will take approximately {(n_follows / 1000):.2f} minutes to scrape."
        )
        # Get new follows and add them to the graph
        extra_edges = get_follows(user["id"], method, users, edges)
        network_container.network.add_edges_from(
            extra_edges[[source, target]].to_numpy()
        )

    if use_recommender:
        analyze_recommend(user["id"], network_container, n, user_helper)
    else:
        analyze(user["id"], network_container, n, user_helper)


def analyze(id, network_container, n, user_helper):
    conn_nodes = top_n(connector_nodes(network_container.network, id), n)
    print(user_helper.pretty_print_users(conn_nodes))


def analyze_recommend(id, network_container, n, user_helper):
    recommendation_engine = Recommendation(network_container)
    most_aligned = recommendation_engine.recommendations(GWWC_NODES, n)
    most_aligned = top_n(gwwc_alignment_fast(), n)
    print(user_helper.pretty_print_users(most_aligned))


def get_follows(user_id, method, users, edges, filter_metric_above=5000):
    url = scrape.url_follows(user_id, method)
    response = scrape.connect_to_endpoint(url, wait=False)
    has_data = response != -1
    # Series of connections to sort by their metric (the top of which will be chosen to
    # explore further)
    ids = {"follower": [], "followed": []}
    while has_data:
        data = response["data"]
        for user in data:
            try:
                user["id"] = int(user["id"])
                # Store user/edge and add to Series of users' followers counts
                if user["id"] not in users["id"].to_numpy():
                    append_user(user)
                if method == "following":
                    if user["id"] not in edges["follower"].to_numpy():
                        ids["follower"].append(user_id)
                        ids["followed"].append(user["id"])
                        append_edge(user_id, user["id"])
                elif method == "followers":
                    if user["id"] not in edges["followed"].to_numpy():
                        ids["follower"].append(user["id"])
                        ids["followed"].append(user_id)
                        append_edge(user["id"], user_id)
            except Exception as e:
                logging.exception(e)
        # Pagination - if >1000 results exist we'll have to make multiple requests
        if "next_token" in response["meta"]:
            response = scrape.connect_to_endpoint(url, response["meta"]["next_token"])
        else:
            has_data = False

    return pd.DataFrame(ids)


def append_edge(follower, followed):
    edge = pd.DataFrame({"follower": follower, "followed": followed}, index=[0])
    edge.to_csv(EDGE_CSV_PATH, mode="a", index=False, header=None)


def append_user(user):
    user = user_frame(user)
    user.to_csv(USERS_FILE_PATH, mode="a", index=False, header=None)


def user_frame(user: dict):
    return pd.DataFrame(
        {
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"],
            "name": user["name"].replace("\0", ""),
            "location": user["location"].replace("\0", "")
            if "location" in user
            else None,
            "description": user["description"].replace("\0", "")
            if "description" in user
            else None,
            "verified": user["verified"],
            "followers_count": user["public_metrics"]["followers_count"],
            "following_count": user["public_metrics"]["following_count"],
            "listed_count": user["public_metrics"]["listed_count"],
            "tweet_count": user["public_metrics"]["tweet_count"],
        },
        index=[0],
    )


def lookup_user(user: str, id=False):
    """Looks up and stores initial users in DB, returning their ids.

    :param user: str
    :param id: boolean indicating whether lookup happens through handle or ID
    """
    url = scrape.url_user_lookup([user], by="id" if id else "handle")
    response = scrape.connect_to_endpoint(
        url, max_results=None, tpr=15 / 300
    )  # 300rp15m
    return response["data"][0]


if __name__ == "__main__":
    # app()
    typer.run(analyze_user)
