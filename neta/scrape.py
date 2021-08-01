# TODO: resume scraping - possibly save chains

import logging
import os
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from queue import SimpleQueue
from typing import List, Union

import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv

from neta.constants import PROJECT_DIR

load_dotenv(dotenv_path=(PROJECT_DIR / ".env"))
dbname = os.environ.get("DBNAME")
user = os.environ.get("DBUSER")
password = os.environ.get("DBPW")
host = os.environ.get("DBHOST")
port = os.environ.get("DBPORT")

bearer_token = os.environ.get("BEARER_TOKEN")

HEADERS = {"Authorization": "Bearer {}".format(bearer_token)}

# Need to correspond to user table in DB!
USER_FIELDS = [
    "id",
    "username",
    "created_at",
    "name",
    "location",
    "description",
    "verified",
]

PUBLIC_METRICS = [
    "followers_count",
    "following_count",
    "listed_count",
    "tweet_count",
]

PARAMS = {
    "user.fields": f"{','.join(USER_FIELDS)},public_metrics",
}

# Global variable to spread out requests over 15-min windows
last_request = -1


def connect_create():
    """
    Opens connection to existing database and creates table to store twitter
    users (if it doesn't exist). Returns database connection.
    """
    # Connect to Twitter Database created in Postgres
    conn = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )
    c = conn.cursor()

    query = (
        "CREATE TABLE IF NOT EXISTS users "
        "(id bigint not null, "
        "username varchar(30), "  # normally 15, historical users with longer name exist
        "created_at timestamp with time zone, "
        "name varchar(140), "  # length subject to change (twitter)
        "location text, "
        "description text, "
        "verified boolean, "
        "followers_count int, "
        "following_count int, "
        "listed_count int, "
        "tweet_count int, "
        "PRIMARY KEY(id));"
    )
    c.execute(query)
    query = (
        "CREATE TABLE IF NOT EXISTS edges "
        "(follower bigint not null references users(id),"
        " followed bigint not null references users(id), "
        "PRIMARY KEY(follower, followed));"
    )
    c.execute(query)
    conn.commit()
    c.close()
    return conn


def store_user(conn, user):
    """
    Store user information in DB via established connection.  Ignores
    duplicates.
    """
    try:
        with conn.cursor() as c:
            c.execute(
                (
                    "INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    "ON CONFLICT DO NOTHING;"
                ),
                (
                    user["id"],
                    user["username"],
                    user["created_at"],
                    user["name"].replace("\0", ""),
                    user["location"].replace("\0", "") if "location" in user else None,
                    user["description"].replace("\0", "")
                    if "description" in user
                    else None,
                    user["verified"],
                    user["public_metrics"]["followers_count"],
                    user["public_metrics"]["following_count"],
                    user["public_metrics"]["listed_count"],
                    user["public_metrics"]["tweet_count"],
                ),
            )
    except Exception as e:
        logging.exception(e)


def store_edge(conn, follower, followed):
    try:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO edges VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                (follower, followed),
            )
    except Exception as e:
        logging.exception(e)


def get_params(pagination_token=None, max_results=1000):
    if max_results is not None:
        return dict(PARAMS, pagination_token=pagination_token, max_results=max_results)
    else:
        return dict(PARAMS, pagination_token=pagination_token)


def url_follows(user_id, follow="following"):
    """Create URL accessing the followers/following APIv2.

    :param user_id: user ID to query followers/ing of
    :param follow: 'following' or 'followers'
    """
    assert follow in ("following", "followers")
    return f"https://api.twitter.com/2/users/{user_id}/{follow}"


def url_user_lookup(users, by="id"):
    lookup = ",".join(map(str, users))
    if by == "id":
        url = f"https://api.twitter.com/2/users?ids={lookup}"
    else:  # handle lookup
        url = f"https://api.twitter.com/2/users/by?usernames={lookup}"
    return url


def connect_to_endpoint(url, next_token=None, tpr=60, max_results=1000, wait=True):
    """Connect to twitter API and return JSON response.  Spreads

    :param url: API URL
    :param next_token: pagination token if multiple pages of results
    :param tpr: time-per-request (60 for follows, as 15 requests allowed per 15min
        window)
    :param max_results: for follower lookup, amount of results per page (max 1000);
        should be None for user lookup
    """
    global last_request
    # Hack to spread out requests over the window - always request every TPR seconds
    t = time.time()
    time_to_wait = tpr - (t - last_request)
    if wait and (time_to_wait > 0):
        time.sleep(time_to_wait)
    else:
        time_to_wait = 0
    last_request = time.time()

    response = requests.request(
        "GET", url, headers=HEADERS, params=get_params(next_token, max_results)
    )
    if response.status_code == 429:
        rem = int(response.headers.get("x-rate-limit-reset"))
        logging.info(f"Rate-limited. Waiting {rem - t} seconds and trying again")
        time.sleep(rem - t)
        response = requests.request(
            "GET",
            url,
            headers=HEADERS,
            params=get_params(next_token, max_results),
        )
    if response.status_code != 200:
        e = Exception(
            f"Request {url} returned an error: {response.status_code} {response.text}"
        )
        logging.exception(e)
        return -1
    logging.info(f"Request {url}: {response.status_code} (waited {time_to_wait:.2f}s)")
    return response.json()


def get_follows(conn, user_id, method="following", filter_metric_above=5000):
    """Get follow{ers/ing} of a twitter user and return the ids of the most followed
    connections.  Stores all queried users/edges in DB and returns follows, sorted
    (descending) by followers count.

    :param conn: database connection
    :param user_id: id of user whose follow{ers/ing} is scraped
    :param method: 'following' or 'followers'
    :param filter_above: Don't consider connections for further scraping if they have
        more than this many following/followers.  This is necessary to prevent scraping
        millions of followers/following, which would take too much time.  Recommended:
        5k for following, 100k for followers.
    """
    url = url_follows(user_id, method)
    response = connect_to_endpoint(url)
    has_data = response != -1

    # Series of connections to sort by their metric (the top of which will be chosen to
    # explore further)
    ids = []
    followers = []
    while has_data:
        data = response["data"]
        for user in data:
            try:
                # Store user/edge and add to Series of users' followers counts
                # User may already be stored, in which case the DB does nothing
                store_user(conn, user)
                if method == "following":
                    store_edge(conn, user_id, user["id"])
                elif method == "followers":
                    store_edge(conn, user["id"], user_id)
                # Check the metric of the method, but store always followers_count
                metric = int(user["public_metrics"][f"{method}_count"])
                if metric <= filter_metric_above:
                    ids.append(int(user["id"]))
                    followers.append(int(user["public_metrics"]["followers_count"]))
            except Exception as e:
                logging.exception(e)
        conn.commit()
        # Pagination - if >1000 results exist we'll have to make multiple requests
        if "next_token" in response["meta"]:
            response = connect_to_endpoint(url, response["meta"]["next_token"])
        else:
            has_data = False

    follows = pd.Series(followers, index=ids)
    return follows.sort_values(ascending=False).index.to_list()


def lookup_initial_ids(conn, users, id=False):
    """Looks up and stores initial users in DB, returning their ids.

    :param conn: database connection
    :param users: list of twitter user ids
    :param id: boolean indicating whether lookup happens through handle or ID
    """
    url = url_user_lookup(users, by="id" if id else "handle")
    response = connect_to_endpoint(url, max_results=None, tpr=15 / 300)  # 300rp15m
    data = response["data"]

    ids = []
    for user in data:
        store_user(conn, user)
        ids.append(user["id"])

    conn.commit()
    return ids


def main(
    users: List[str],
    topn: int = 15,
    n_degrees: int = 6,
    method: str = "following",
    filter_metric_above=5000,
    edges_dir: Union[Path, str] = ".",
    save_every: int = 10,
):
    """Scrape Twitter follows and write edge list to database.

    :param users: Twitter handles or IDs (don't mix!) to start building the graph from,
        need to be less than 100.
    :param topn: build edges for the topn follows, based on followers count
    :param n_degrees: depth of the graph (exponential, don't set too high!)
    :param method: 'following' or 'followers'
    :param filter_metric_above: Don't consider connections for further scraping if they
        have more than this many following/followers.  This is necessary to prevent
        scraping millions of followers/following, which would take too much time.
        Recommended: 5k for following, 100k for followers.
    :param edges_dir: directory to save edges.pkl in
    :param save_every: save edges.pkl (edge list) every n scraped users (edges are also
        saved to DB - this is for ad-hoc checks)
    """
    edges_dir = Path(edges_dir)
    logging.basicConfig(
        filename=edges_dir / "scrape.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)-15s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ef = edges_dir / "edges.pkl"

    if ef.is_file():
        edges = pd.read_pickle(ef)
    else:
        edges = pd.Series(dtype=int)

    # edges = pd.Series(dtype=int)
    conn = connect_create()
    logging.info("Connected to database.")

    # Check whether the initial users are ids or handles
    if pd.Series(users, dtype=str).str.isnumeric().all():
        id = True
    else:
        id = False
    ids = lookup_initial_ids(conn, users, id=id)
    logging.info("Stored initial ids in DB.")

    q = SimpleQueue()  # type: SimpleQueue[List[int]]
    for user_id in ids:
        q.put([0, user_id])
    i = 0

    # Use [-1] as iter sentinel (see else at end of statement)
    for follow_chain in iter(q.get, [-1]):
        user_id = follow_chain[-1]
        parent_id = follow_chain[-2]

        # Check if user is in (index of) edges: for both followers & following it means
        # they've been scraped already. Note the DB always stores follower/following
        # pairs, hence edges Series and edges DB table are inverted for followers
        if user_id in edges:
            logging.info(
                f"Skipping user {user_id} (parent {parent_id}) [already in edges]"
            )
            continue

        logging.info(f"Scraping follows of user {user_id} (parent {parent_id}).")
        try:
            follows = get_follows(conn, user_id, method)
            edges = edges.append(
                pd.Series(follows, index=[user_id] * len(follows), dtype=int)
            )
            # Until the desired max degree is reached, add to the follow chain the n
            # most followed connections to continue scraping
            if not q.empty() and ((len(follow_chain) - 1) < n_degrees):
                for follow_id in follows[:topn]:
                    q.put(follow_chain + [follow_id])
            else:
                # Since we are doing breadth-first search, this will ensure we terminate
                # at the end, without cutting short another path of execution
                q.put([-1])
        except Exception as e:
            logging.error(f"ID {user_id} failed (could be e.g. private or suspended)")
            logging.exception(e)

        if i % save_every == 0:
            edges.to_pickle(ef)
            # Dump queue for easy resumption of scraper, then add back in
            qc = []
            while not q.empty():
                qc.append(q.get())
            pd.Series([x[-1] for x in qc]).to_pickle(edges_dir / "queue.pkl")
            for x in qc:
                q.put(x)
        i += 1

    conn.close()


if __name__ == "__main__":
    parser = ArgumentParser(description="Scrape twitter follows into network graph.")
    parser.add_argument(
        "users",
        default=["givingwhatwecan"],
        type=str,
        nargs="*",
        help="Twitter handles or IDs (don't mix!) to start building the graph from, "
        "need to be less than 100. (Default: ['givingwhatwecan'])",
    )
    parser.add_argument(
        "-n",
        dest="topn",
        default=15,
        type=int,
        help="Build edges for the topn follows, based on followers count.",
    )
    parser.add_argument(
        "-d",
        dest="n_degrees",
        default=6,
        type=int,
        help="Depth of the graph (exponential, don't set too high!)",
    )
    parser.add_argument(
        "-m",
        dest="method",
        default="following",
        type=str,
        help="'following' to scrape who users follow, 'followers' to scrape who follows"
        "them.",
    )
    parser.add_argument(
        "-f",
        dest="filter_metric_above",
        default=5000,
        type=int,
        help="Don't consider connections for further scraping if they have more than "
        "this many following/followers. (depends on method)",
    )
    parser.add_argument(
        "--edges_dir",
        default=".",
        type=str,
        help="Directory to save edges.pkl in. (needs to exist)",
    )
    parser.add_argument(
        "--save_every",
        default=50,
        type=int,
        help="Save edges.pkl (edge list) every n scraped users"
        "(edges are also saved to DB - this is for ad-hoc checks)",
    )

    args = parser.parse_args()
    main(**args.__dict__)
