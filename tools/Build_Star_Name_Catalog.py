import csv
import re
import time
from pathlib import Path

from astroquery.simbad import Simbad


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATA_DIR = (
    PROJECT_DIR
    / "data"
)

INPUT_FILE = (
    DATA_DIR
    / "gaia_200ly.csv"
)

OUTPUT_FILE = (
    DATA_DIR
    / "star_names.csv"
)


# ============================================================
# SETTINGS
# ============================================================

BATCH_SIZE = 100

RETRY_DELAY = 5

BATCH_DELAY = 0.5


# ============================================================
# CANONICAL NAMES
# ============================================================

CANONICAL_NAMES = {

    5853498713190525696:
        "Proxima Centauri",

    4472832130942575872:
        "Barnard's Star",

    2947050466531873024:
        "Sirius B",
}


# ============================================================
# GREEK LETTER NAMES
# ============================================================

GREEK_NAMES = {

    "alf": "Alpha",
    "bet": "Beta",
    "gam": "Gamma",
    "del": "Delta",
    "eps": "Epsilon",
    "zet": "Zeta",
    "eta": "Eta",
    "tet": "Theta",
    "iot": "Iota",
    "kap": "Kappa",
    "lam": "Lambda",
    "mu.": "Mu",
    "nu.": "Nu",
    "ksi": "Xi",
    "omi": "Omicron",
    "pi.": "Pi",
    "rho": "Rho",
    "sig": "Sigma",
    "tau": "Tau",
    "ups": "Upsilon",
    "phi": "Phi",
    "chi": "Chi",
    "psi": "Psi",
    "ome": "Omega",
}


# ============================================================
# CONSTELLATION NAMES
# ============================================================

CONSTELLATION_NAMES = {

    "And": "Andromedae",
    "Aql": "Aquilae",
    "Ari": "Arietis",
    "Aur": "Aurigae",
    "Boo": "Boötis",
    "CMa": "Canis Majoris",
    "CMi": "Canis Minoris",
    "Cas": "Cassiopeiae",
    "Cet": "Ceti",
    "Cnc": "Cancri",
    "CrB": "Coronae Borealis",
    "Cyg": "Cygni",
    "Dra": "Draconis",
    "Eri": "Eridani",
    "Gem": "Geminorum",
    "Her": "Herculis",
    "Hyi": "Hydri",
    "Leo": "Leonis",
    "LMi": "Leonis Minoris",
    "Lyn": "Lyncis",
    "Lyr": "Lyrae",
    "Oph": "Ophiuchi",
    "Pav": "Pavonis",
    "Per": "Persei",
    "PsA": "Piscis Austrini",
    "Psc": "Piscium",
    "Sge": "Sagittae",
    "Ser": "Serpentis",
    "Tau": "Tauri",
    "Tri": "Trianguli",
    "UMa": "Ursae Majoris",
}


# ============================================================
# LOAD GAIA IDS
# ============================================================

def load_gaia_source_ids(
    filename
):

    source_ids = []

    with open(
        filename,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            source_ids.append(
                int(
                    row["source_id"]
                )
            )

    return source_ids


# ============================================================
# LOAD EXISTING NAMES
# ============================================================

def load_existing_names(
    filename
):

    names = {}

    if not filename.exists():

        return names

    with open(
        filename,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            source_id = int(
                row["source_id"]
            )

            name = (
                row["common_name"]
                .strip()
            )

            if name:

                names[
                    source_id
                ] = name

    return names


# ============================================================
# NORMALIZE BAYER NAME
# ============================================================

def normalize_bayer_name(
    name
):

    if name.startswith(
        "* "
    ):

        name = name[2:]

    parts = name.split()

    if not parts:

        return name

    if (
        parts[0].lower()
        in GREEK_NAMES
    ):

        parts[0] = (
            GREEK_NAMES[
                parts[0].lower()
            ]
        )

    for i, part in enumerate(
        parts
    ):

        if (
            part
            in CONSTELLATION_NAMES
        ):

            parts[i] = (
                CONSTELLATION_NAMES[
                    part
                ]
            )

    return " ".join(
        parts
    )


# ============================================================
# NORMALIZE DISPLAY NAME
# ============================================================

def normalize_display_name(
    name
):

    name = re.sub(
        r"\s+",
        " ",
        name
    ).strip()

    replacements = {
        "LAL ": "Lalande ",
    }

    for old, new in (
        replacements.items()
    ):

        if name.upper().startswith(
            old.upper()
        ):

            name = (
                new
                +
                name[len(old):]
            )

    if name.startswith(
        "* "
    ):

        name = (
            normalize_bayer_name(
                name
            )
        )

    return name


# ============================================================
# IDENTIFIER SCORE
# ============================================================

def score_identifier(
    identifier
):

    name = (
        identifier
        .strip()
    )

    upper = name.upper()

    # --------------------------------------------------------
    # Proper names
    # --------------------------------------------------------

    if upper.startswith(
        "NAME "
    ):

        return 0

    # --------------------------------------------------------
    # Bayer / Flamsteed
    # --------------------------------------------------------

    if upper.startswith(
        "* "
    ):

        return 10

    # --------------------------------------------------------
    # Familiar nearby-star catalogs
    # --------------------------------------------------------

    if upper.startswith(
        "WOLF "
    ):

        return 20

    if upper.startswith(
        "ROSS "
    ):

        return 20

    if upper.startswith(
        "LAL "
    ):

        return 20

    if upper.startswith(
        "LALANDE "
    ):

        return 20

    # --------------------------------------------------------
    # Gliese
    # --------------------------------------------------------

    if upper.startswith(
        "GJ "
    ):

        return 30

    if upper.startswith(
        "GL "
    ):

        return 30

    # --------------------------------------------------------
    # Other stellar catalogs
    # --------------------------------------------------------

    if upper.startswith(
        "LHS "
    ):

        return 40

    if upper.startswith(
        "LTT "
    ):

        return 45

    if upper.startswith(
        "LP "
    ):

        return 50

    # --------------------------------------------------------
    # HIP / HD
    # --------------------------------------------------------

    if upper.startswith(
        "HIP "
    ):

        return 60

    if upper.startswith(
        "HD "
    ):

        return 65

    # --------------------------------------------------------
    # Other catalogs
    # --------------------------------------------------------

    if upper.startswith(
        "MCC "
    ):

        return 80

    if upper.startswith(
        "ZKH "
    ):

        return 80

    # --------------------------------------------------------
    # Gaia fallback
    # --------------------------------------------------------

    if upper.startswith(
        "GAIA "
    ):

        return 100

    return 75


# ============================================================
# CHOOSE DISPLAY NAME
# ============================================================

def choose_display_name(
    identifiers
):

    if not identifiers:

        return None

    identifiers = [

        identifier.strip()

        for identifier
        in identifiers

        if identifier.strip()
    ]

    if not identifiers:

        return None

    identifiers.sort(
        key=lambda identifier: (
            score_identifier(
                identifier
            ),
            len(
                identifier
            )
        )
    )

    best_name = (
        identifiers[0]
    )

    if best_name.upper().startswith(
        "NAME "
    ):

        best_name = (
            best_name[5:]
        )

    return normalize_display_name(
        best_name
    )


# ============================================================
# QUERY SIMBAD
# ============================================================

def query_simbad_batch(
    source_ids
):

    gaia_names = [

        f"Gaia DR3 {source_id}"

        for source_id
        in source_ids
    ]

    quoted_names = ", ".join(
        f"'{name}'"
        for name
        in gaia_names
    )

    query = f"""
        SELECT
            input_id.id AS gaia_id,
            ident.id AS identifier

        FROM ident AS input_id

        JOIN basic
            ON input_id.oidref = basic.oid

        JOIN ident
            ON basic.oid = ident.oidref

        WHERE input_id.id IN (
            {quoted_names}
        )
    """

    return Simbad.query_tap(
        query
    )


# ============================================================
# WRITE NAME CATALOG
# ============================================================

def write_star_names(
    filename,
    star_names
):

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow([
            "source_id",
            "common_name"
        ])

        for source_id in sorted(
            star_names
        ):

            writer.writerow([
                source_id,
                star_names[
                    source_id
                ]
            ])


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "       STAR NAME CATALOG BUILDER"
    )

    print(
        "========================================"
    )

    print()

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Could not find Gaia catalog:\n"
            f"{INPUT_FILE}"
        )

    # --------------------------------------------------------
    # Load Gaia source IDs
    # --------------------------------------------------------

    print(
        f"Loading Gaia catalog:"
    )

    print(
        f"  {INPUT_FILE}"
    )

    source_ids = (
        load_gaia_source_ids(
            INPUT_FILE
        )
    )

    print(
        f"Loaded "
        f"{len(source_ids):,} "
        f"Gaia source IDs."
    )

    # --------------------------------------------------------
    # Load existing names
    # --------------------------------------------------------

    existing_names = (
        load_existing_names(
            OUTPUT_FILE
        )
    )

    print(
        f"Loaded "
        f"{len(existing_names):,} "
        f"existing names."
    )

    # --------------------------------------------------------
    # Determine missing IDs
    # --------------------------------------------------------

    missing_ids = [

        source_id

        for source_id
        in source_ids

        if source_id
        not in existing_names
    ]

    print(
        f"Names still needed: "
        f"{len(missing_ids):,}"
    )

    # --------------------------------------------------------
    # Nothing to do
    # --------------------------------------------------------

    if not missing_ids:

        print()
        print(
            "Name catalog is already "
            "up to date."
        )

        return

    # --------------------------------------------------------
    # Batch information
    # --------------------------------------------------------

    total_batches = (
        len(missing_ids)
        +
        BATCH_SIZE
        -
        1
    ) // BATCH_SIZE

    print()
    print(
        f"Processing "
        f"{total_batches:,} "
        f"SIMBAD batches."
    )

    # --------------------------------------------------------
    # Process batches
    # --------------------------------------------------------

    for batch_number, start in enumerate(

        range(
            0,
            len(missing_ids),
            BATCH_SIZE
        ),

        start=1
    ):

        batch = missing_ids[
            start:
            start + BATCH_SIZE
        ]

        print()
        print(
            f"Batch "
            f"{batch_number:,}"
            f"/"
            f"{total_batches:,}"
            f" "
            f"("
            f"{len(batch):,}"
            f" stars)"
        )

        # --------------------------------------------
        # Query with retries
        # --------------------------------------------

        result = None

        for attempt in range(
            3
        ):

            try:

                result = (
                    query_simbad_batch(
                        batch
                    )
                )

                break

            except Exception as error:

                print(
                    f"SIMBAD query failed "
                    f"(attempt "
                    f"{attempt + 1}/3): "
                    f"{error}"
                )

                if attempt < 2:

                    print(
                        f"Waiting "
                        f"{RETRY_DELAY} "
                        f"seconds..."
                    )

                    time.sleep(
                        RETRY_DELAY
                    )

        # --------------------------------------------
        # If batch failed, leave it unresolved
        # and continue.
        # --------------------------------------------

        if result is None:

            print(
                "Batch failed. "
                "Continuing."
            )

            continue

        # --------------------------------------------
        # Group identifiers
        # --------------------------------------------

        identifiers_by_gaia = {}

        for row in result:

            gaia_id = str(
                row["gaia_id"]
            ).strip()

            identifier = str(
                row["identifier"]
            ).strip()

            identifiers_by_gaia.setdefault(
                gaia_id,
                []
            ).append(
                identifier
            )

        # --------------------------------------------
        # Select best name
        # --------------------------------------------

        found_this_batch = 0

        for source_id in batch:

            # ----------------------------------------
            # Manual overrides
            # ----------------------------------------

            if (
                source_id
                in CANONICAL_NAMES
            ):

                display_name = (
                    CANONICAL_NAMES[
                        source_id
                    ]
                )

            else:

                gaia_name = (
                    f"Gaia DR3 "
                    f"{source_id}"
                )

                identifiers = (
                    identifiers_by_gaia.get(
                        gaia_name,
                        []
                    )
                )

                display_name = (
                    choose_display_name(
                        identifiers
                    )
                )

            # ----------------------------------------
            # Store name if one was found
            # ----------------------------------------

            if display_name:

                existing_names[
                    source_id
                ] = display_name

                found_this_batch += 1

        # --------------------------------------------
        # SAVE AFTER EVERY BATCH
        # --------------------------------------------

        write_star_names(
            OUTPUT_FILE,
            existing_names
        )

        print(
            f"Names found this batch: "
            f"{found_this_batch:,}"
        )

        print(
            f"Total names stored: "
            f"{len(existing_names):,}"
        )

        remaining = (
            len(source_ids)
            -
            len(existing_names)
        )

        print(
            f"Remaining unnamed systems: "
            f"{remaining:,}"
        )

        # --------------------------------------------
        # Be polite to SIMBAD
        # --------------------------------------------

        time.sleep(
            BATCH_DELAY
        )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print(
        "========================================"
    )

    print(
        "          NAME BUILD COMPLETE"
    )

    print(
        "========================================"
    )

    print(
        f"Gaia systems: "
        f"{len(source_ids):,}"
    )

    print(
        f"Named systems: "
        f"{len(existing_names):,}"
    )

    print(
        f"Unnamed systems: "
        f"{len(source_ids) - len(existing_names):,}"
    )

    print()

    print(
        f"Output:"
    )

    print(
        f"  {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()