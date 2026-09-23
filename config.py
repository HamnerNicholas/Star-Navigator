from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

DATA_DIR = (
    BASE_DIR
    / "data"
)


# ============================================================
# DATA FILES
# ============================================================

CATALOG_FILE = (
    DATA_DIR
    / "gaia_200ly.csv"
)

STAR_NAME_FILE = (
    DATA_DIR
    / "star_names.csv"
)


# ============================================================
# CONSTELLATION DATA
# ============================================================

CONSTELLATION_DIR = (
    DATA_DIR
    / "constellations"
)

CONSTELLATION_LINES_FILE = (
    CONSTELLATION_DIR
    / "western_index.json"
)

CONSTELLATION_GAIA_FILE = (
    CONSTELLATION_DIR
    / "constellation_stars.csv"
)

# ============================================================
# NAVIGATION SETTINGS
# ============================================================

MAX_JUMP_DISTANCE = 10.0


# ============================================================
# RENDERER SETTINGS
# ============================================================

BACKGROUND_RADIUS = 70.0

INTERACTIVE_MAP_FILE = (
    BASE_DIR
    / "interactive_star_map.html"
)

STATIC_MAP_FILE = (
    BASE_DIR
    / "star_route.png"
)