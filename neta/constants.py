from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
EDGE_CSV_PATH = (PROJECT_DIR / "data/edges_following25.csv").resolve()
USERS_FILE_PATH = (PROJECT_DIR / "data/users_following25.csv").resolve()
NETWORK_CACHE_PATH = str((PROJECT_DIR / "tmp/network_cache_{}.pkl").resolve())
