import networkx as nx
import re
import os
import csv

DATA_FOLDER_NAME = 'data'


def construct_follower_graph():
    twitter_csv_regex = re.compile(r"GWWC Top Twitter Followers - ([^\s]+) _5000.csv")
    follower_graph = nx.Graph()
    for data_filename in os.listdir(DATA_FOLDER_NAME):
        file_match = twitter_csv_regex.match(data_filename)
        if file_match:
            followed_account = file_match[1]
            with open(os.path.join(DATA_FOLDER_NAME, file_match[0])) as data_file:
                data_csv_reader = csv.reader(data_file)
                account_relationships = [(row[1], followed_account) for row in data_csv_reader]
                follower_graph.add_edges_from(account_relationships)
    return follower_graph


follow_graph = construct_follower_graph()
centrality = nx.eigenvector_centrality(follow_graph)
top_opinions = [twitter_name for twitter_name, centrality_score in
                sorted(centrality.items(), key=lambda item: item[1],
                       reverse=True)][:100]
