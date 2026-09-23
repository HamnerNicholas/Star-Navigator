import csv

from astroquery.gaia import Gaia

from pathlib import Path


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

OUTPUT_FILE = (
    DATA_DIR
    / "gaia_200ly.csv"
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# SETTINGS
# ============================================================

MAX_DISTANCE_LY = 200.0

# Gaia parallax is in milliarcseconds.
PARALLAX_MIN_MAS = (
    1000.0
    /
    (MAX_DISTANCE_LY / 3.26156)
)

# ============================================================
# GAIA QUERY
# ============================================================

QUERY = f"""
SELECT
    source_id,
    ra,
    dec,
    parallax,
    phot_g_mean_mag,
    bp_rp,
    pmra,
    pmdec,
    radial_velocity
FROM gaiadr3.gaia_source
WHERE parallax >= {PARALLAX_MIN_MAS}
"""


# ============================================================
# RUN QUERY
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "      GAIA CATALOG BUILDER"
    )

    print(
        "========================================"
    )

    print()

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print(
        f"Target radius: "
        f"{MAX_DISTANCE_LY:.0f} ly"
    )

    print(
        f"Minimum parallax: "
        f"{PARALLAX_MIN_MAS:.4f} mas"
    )

    print()

    print(
        "Submitting Gaia query..."
    )

    job = Gaia.launch_job_async(
        QUERY,
        verbose=True
    )

    results = job.get_results()

    print(
        f"Received "
        f"{len(results):,} Gaia sources."
    )

    # ========================================================
    # WRITE CSV
    # ========================================================

    fieldnames = [
        "source_id",
        "designation",
        "ra",
        "dec",
        "parallax",
        "phot_g_mean_mag",
        "bp_rp",
        "pmra",
        "pmdec",
        "radial_velocity",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow(
            fieldnames
        )

        writer.writerow([
            "source_id",
            "designation",
            "ra",
            "dec",
            "parallax",
            "phot_g_mean_mag",
            "bp_rp",
            "pmra",
            "pmdec",
            "radial_velocity",
        ])

        for row in results:

            writer.writerow([
                row["source_id"],
                f"Gaia DR3 {row['source_id']}",
                row["ra"],
                row["dec"],
                row["parallax"],
                row["phot_g_mean_mag"],
                row["bp_rp"],
                row["pmra"],
                row["pmdec"],
                row["radial_velocity"],
            ])

    print()
    print(
        f"Saved catalog to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()