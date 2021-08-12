# Giving what we can Twitter network analysis

This project analyzes Twitter users connected with Giving What We Can (GWWC) through a
network analysis. We scrape a network graph around GWWC and analyze it with networkx.

## Analysis

To use this toolbox to analyze the scraped network (see [Scraping][Scraping]), there are
two options:

1. Query single user (who will be scraped if not already in the network) to compute
   'connector nodes' to the network for. If scraped, the user will be saved to the
   network.
2. Compute network-wide alignment based on a number of seed-accounts in an interactive
   environment (we will use an IPython shell)
   
### Requirements

#### Python
You need to have Python (3.8+) installed with a number of [requirements](requirements.txt).
To install the requirements, you can run:

`pip install -r requirements.txt`

Then, you need to install this package by running:

`pip install -e .`

If you want to analyze an existing network interactively, you also need to `pip install
ipython`.

#### Network graph files
Copy the `users_following25.csv` and `edges_following25.csv` files from the GWWC drive
into the `data/` folder. If you want to use followers data, copy the files into that
same directory, and change `EDGE_CSV_PATH` and `USERS_FILE_PATH` in `neta/constants.py`
to point to those files.

#### Twitter API access
To use method 1. (and allow scraping) you need to have a [Twitter developer
account](https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api)
with API credentials. We will need the bearer token for the API access (you can find it
at the developer dashboard in your Twitter project under 'Projects & Apps' - if you
forgot the token, you may have to regenerate one).

Copy the bearer token into a file called `.env` at the root of this project
(`gwwc-twitter-network/.env`) such that it contains:
`BEARER_TOKEN=#########################`, substituting `#...#` for your token.


### Use

#### 1. Query (& scrape) single user
Type the following to see available options:
```bash
> python neta/analyze_user.py --help
Usage: analyze_user.py [OPTIONS] LOOKUP

Arguments:
  LOOKUP  Twitter ID or handle to analyze  [required]

Options:
  --method TEXT         Analyze 'following' or 'followers' (needs to match
                        files constants.py)  [default: following]

  --n INTEGER           No. of results to return, ie. 50 recommendations
                        [default: 50]

  --use-recommender     Pass to use recommender method.  [default: False]
  --undirected          Use an undirected graph. (not recommended)  [default:
                        False]

  --out-dir PATH        Directory to save csv output to. Uses lookup username
                        as filename (ie. results/givingwhatwecan.csv).
                        [default: results]

  --logfile TEXT        File to save logs to (full path).  [default:
                        ./analyze.log]
```

For example, to get the top 100 'connecting' nodes from GWWC-aligned accounts to the
user 'excellentrandom' according to the Jaccard Similarity-based method, we can run:

```
python neta/analyze_user.py excellentrandom --n 100
```

To add a user to the graph, and then run the general recommendation algorithm (start
many random walks from the GWWC seed nodes) for 500 recommendations, do the following:

```
python neta/analyze_user.py excellentrandom --n 500 --use-recommender
```

#### 2. Analyze network in IPython

1. In the console, navigate to this folder and type `ipython` to open up the interactive
python console.
2. Run `%run neta/repl.py` to load all necessary components

Now you can run the following commands:

```python
# Number of results to request
n = 25
# For network centrality
most_central = top_n(centrality(network), n)

# For Jaccard alignment
most_aligned = top_n(gwwc_alignment_fast(network), n)

# To query an ID that is in the network for connector nodes
query_account = 14717311  # @elonmusk
conn_nodes = top_n(connector_nodes(network, query_account), n)
    
# To use the recommendation approach, starting from GWWC seed nodes
most_recommended = recommendation_engine.recommendations(GWWC_NODES, n)

# To print out the results, use this (most_xxx as the input):
print(user_helper.pretty_print(most_recommended))
```

## Scraping

### Requirements

* Postgresql database to use with [psycopg2](https://www.psycopg.org/)
* `.env` file ([python-dotenv](https://github.com/theskumar/python-dotenv)) at the root
  of this project containing the following environment variables:
    - DBNAME - database name
    - DBUSER - database user
    - DBPW   - database password
    - DBHOST - database host
    - DBPORT - database port
    - BEARER_TOKEN - bearer token for Twitter API authentication (make sure you have a
      developer account with
      [access](https://developer.twitter.com/en/products/twitter-api))

### Use

The scraper lives in `./neta/scraper.py` and can be called with the following:

```
> python neta/scrape.py -h
usage: scrape.py [-h] [-n TOPN] [-d N_DEGREES] [-m METHOD] [-f FILTER_METRIC_ABOVE]
                 [--edges_dir EDGES_DIR] [--save_every SAVE_EVERY]
                 [ids ...]

Scrape twitter follows into network graph.

positional arguments:
  users                 Twitter handles or IDs (don't mix!) to start building the graph
                        from, need to be less than 100. (Default: ['givingwhatwecan'])

optional arguments:
  -h, --help            show this help message and exit
  -n TOPN               Build edges for the topn follows, based on followers count.
  -d N_DEGREES          Depth of the graph (exponential, don't set too high!)
  -m METHOD             'following' to scrape who users follow, 'followers' to scrape who
                        followsthem.
  -f FILTER_METRIC_ABOVE
                        Don't consider connections for further scraping if they have more
                        than this many following/followers. (depends on method)
  --edges_dir EDGES_DIR
                        Directory to save edges.pkl in. (needs to exist)
  --save_every SAVE_EVERY
                        Save edges.pkl (edge list) every n scraped users(edges are also
                        saved to DB - this is for ad-hoc checks)
```
