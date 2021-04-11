# Giving what we can Twitter network analysis

This project analyzes Twitter users connected with Giving What We Can (GWWC) through a
network analysis. We scrape a network graph around GWWC and analyze it with networkx.

## Scraping

### Requirements

* Postgresql database to use with [psycopg2](https://www.psycopg.org/)
* `.env` file ([python-dotenv](https://github.com/theskumar/python-dotenv)) at the root of this project containing the following environment variables:
    - DBNAME - database name
    - DBUSER - database user
    - DBPW   - database password
    - DBHOST - database host
    - DBPORT - database port
    - BEARER_TOKEN - bearer token for Twitter API authentication (make sure you have a developer account with [access](https://developer.twitter.com/en/products/twitter-api))

### Use

The scraper lives in `./neta/scraper.py` and can be called with the following:

```
> python scrape.py -h
usage: scrape.py [-h] [-n TOPN] [-d N_DEGREES] [-m METHOD] [-f FILTER_METRIC_ABOVE]
                 [--edges_dir EDGES_DIR] [--save_every SAVE_EVERY]
                 [ids ...]

Scrape twitter follows into network graph.

positional arguments:
  ids                   Twitter handles or IDs (don't mix!) to start building the graph
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
