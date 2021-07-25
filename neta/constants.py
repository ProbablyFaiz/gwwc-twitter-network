from pathlib import Path

top = Path(__file__).parent.parent
EDGE_CSV_PATH = (top / "data/edges_following25.csv").resolve()
NETWORK_CACHE_PATH = (top / "tmp/network_cache.pik").resolve()
USERS_FILE_PATH = (top / "data/users_following25.csv").resolve()
