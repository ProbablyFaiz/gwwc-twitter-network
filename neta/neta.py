import logging
from pathlib import Path

import numpy as np
import pandas as pd
import typer

from neta import constants, scrape

app = typer.Typer()


def analyze_user(user: str, log_dir: Path = Path(".")):
    logging.basicConfig(
        filename=log_dir / "scrape.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)-15s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    print(user, log_dir.resolve())

    id = True if user.isnumeric() else False
    lookup_user(user, constants.USERS_FILE_PATH, id)


def lookup_user(user, user_csv, id=False):
    """Looks up and stores initial users in DB, returning their ids.

    :param conn: database connection
    :param users: list of twitter user ids
    :param id: boolean indicating whether lookup happens through handle or ID
    """
    url = scrape.url_user_lookup([user], by="id" if id else "handle")
    response = scrape.connect_to_endpoint(
        url, max_results=None, tpr=15 / 300
    )  # 300rp15m
    user = response["data"][0]

    user = pd.DataFrame(
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
    user.to_csv(user_csv, mode="a", index=False, header=None)


if __name__ == "__main__":
    # app()
    typer.run(analyze_user)
