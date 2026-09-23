import json
import csv

from pathlib import Path

from astroquery.gaia import Gaia
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

CONSTELLATION_DIR = (
    DATA_DIR
    / "constellations"
)

INPUT_FILE = (
    CONSTELLATION_DIR
    / "western_index.json"
)

OUTPUT_FILE = (
    CONSTELLATION_DIR
    / "constellation_stars.csv"
)


# ============================================================
# LOAD STELLARIUM DATA
# ============================================================

def load_constellation_data():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


# ============================================================
# EXTRACT HIP IDS
# ============================================================

def extract_constellation_data(
    data
):

    constellations = []

    hip_ids = set()

    for constellation in data[
        "constellations"
    ]:

        iau = constellation.get(
            "iau"
        )

        common_name = (
            constellation
            .get(
                "common_name",
                {}
            )
            .get(
                "native"
            )
        )

        if not iau:
            continue

        lines = constellation.get(
            "lines",
            []
        )

        normalized_lines = []

        for line in lines:

            normalized_line = []

            for value in line:

                # Stellarium uses strings such
                # as "thin" as line-style markers.

                if isinstance(
                    value,
                    str
                ):

                    if value == "thin":
                        continue

                    raise ValueError(
                        f"Unknown constellation "
                        f"line marker: {value}"
                    )

                hip_id = int(
                    value
                )

                normalized_line.append(
                    hip_id
                )

                hip_ids.add(
                    hip_id
                )

            if normalized_line:

                normalized_lines.append(
                    normalized_line
                )

        constellations.append({
            "iau": iau,
            "name": (
                common_name
                or iau
            ),
            "lines": normalized_lines
        })

    return (
        constellations,
        sorted(
            hip_ids
        )
    )


# ============================================================
# GAIA CROSSMATCH
# ============================================================

def query_gaia_hipparcos(
    hip_ids
):

    hip_list = ", ".join(
        str(hip_id)
        for hip_id in hip_ids
    )

    query = f"""
        SELECT

            h.original_ext_source_id
                AS hip_id,

            g.source_id
                AS gaia_source_id,

            g.ra
                AS ra_deg,

            g.dec
                AS dec_deg

        FROM gaiadr3.hipparcos2_best_neighbour h

        JOIN gaiadr3.gaia_source g
            ON h.source_id = g.source_id

        WHERE h.original_ext_source_id IN (
            {hip_list}
        )
    """

    print(
        "Submitting Gaia Hipparcos "
        "crossmatch..."
    )

    job = Gaia.launch_job_async(
        query,
        verbose=True
    )

    return job.get_results()


# ============================================================
# SIMBAD FALLBACK
# ============================================================

def query_simbad_fallback(
    hip_ids
):

    if not hip_ids:

        return {}

    names = [
        f"HIP {hip_id}"
        for hip_id in hip_ids
    ]

    quoted_names = ", ".join(
        f"'{name}'"
        for name in names
    )

    query = f"""
        SELECT

            input_id.id
                AS hip_id,

            basic.ra
                AS ra_deg,

            basic.dec
                AS dec_deg

        FROM ident AS input_id

        JOIN basic
            ON input_id.oidref = basic.oid

        WHERE input_id.id IN (
            {quoted_names}
        )
    """

    print(
        "Submitting SIMBAD fallback "
        "query..."
    )

    result = Simbad.query_tap(
        query
    )

    fallback = {}

    for row in result:

        hip_name = str(
            row["hip_id"]
        ).strip()

        if not hip_name.upper().startswith(
            "HIP "
        ):

            continue

        try:

            hip_id = int(
                hip_name.split()[1]
            )

            ra = float(
                row["ra_deg"]
            )

            dec = float(
                row["dec_deg"]
            )

        except (
            ValueError,
            TypeError
        ):

            continue

        fallback[
            hip_id
        ] = {
            "ra_deg": ra,
            "dec_deg": dec
        }

    return fallback


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "    CONSTELLATION CATALOG BUILDER"
    )

    print(
        "========================================"
    )

    print()

    # ========================================================
    # LOAD STELLARIUM DATA
    # ========================================================

    data = (
        load_constellation_data()
    )

    (
        constellations,
        hip_ids
    ) = extract_constellation_data(
        data
    )

    print(
        f"Loaded "
        f"{len(constellations):,} "
        f"constellations."
    )

    print(
        f"Unique HIP stars: "
        f"{len(hip_ids):,}"
    )

    print()

    # ========================================================
    # PRIMARY GAIA CROSSMATCH
    # ========================================================

    gaia_result = (
        query_gaia_hipparcos(
            hip_ids
        )
    )

    gaia_matches = {}

    for row in gaia_result:

        hip_id = int(
            row["hip_id"]
        )

        gaia_source_id = int(
            row["gaia_source_id"]
        )

        ra_deg = float(
            row["ra_deg"]
        )

        dec_deg = float(
            row["dec_deg"]
        )

        gaia_matches[
            hip_id
        ] = {
            "gaia_source_id":
                gaia_source_id,

            "ra_deg":
                ra_deg,

            "dec_deg":
                dec_deg,

            "source":
                "gaia"
        }

    print()

    print(
        f"Gaia crossmatched: "
        f"{len(gaia_matches):,}"
    )

    # ========================================================
    # FIND UNMATCHED HIP STARS
    # ========================================================

    unmatched = [
        hip_id
        for hip_id in hip_ids
        if hip_id not in gaia_matches
    ]

    print(
        f"Gaia unmatched: "
        f"{len(unmatched):,}"
    )

    # ========================================================
    # SIMBAD FALLBACK
    # ========================================================

    simbad_matches = (
        query_simbad_fallback(
            unmatched
        )
    )

    print()

    print(
        f"SIMBAD fallback matches: "
        f"{len(simbad_matches):,}"
    )

    # ========================================================
    # COMBINE RESULTS
    # ========================================================

    constellation_stars = {}

    for hip_id in hip_ids:

        if hip_id in gaia_matches:

            constellation_stars[
                hip_id
            ] = gaia_matches[
                hip_id
            ]

            continue

        if hip_id in simbad_matches:

            constellation_stars[
                hip_id
            ] = {
                "gaia_source_id":
                    None,

                "ra_deg":
                    simbad_matches[
                        hip_id
                    ]["ra_deg"],

                "dec_deg":
                    simbad_matches[
                        hip_id
                    ]["dec_deg"],

                "source":
                    "simbad"
            }

    # ========================================================
    # WRITE OUTPUT
    # ========================================================

    CONSTELLATION_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(
            file
        )

        writer.writerow([
            "hip_id",
            "ra_deg",
            "dec_deg",
            "gaia_source_id",
            "source"
        ])

        for hip_id in sorted(
            constellation_stars
        ):

            star = (
                constellation_stars[
                    hip_id
                ]
            )

            writer.writerow([
                hip_id,
                star["ra_deg"],
                star["dec_deg"],
                star["gaia_source_id"],
                star["source"]
            ])

    # ========================================================
    # FINAL REPORT
    # ========================================================

    total = (
        len(hip_ids)
    )

    gaia_count = (
        len(gaia_matches)
    )

    simbad_count = (
        len(simbad_matches)
    )

    resolved = (
        gaia_count
        +
        simbad_count
    )

    unresolved = (
        total
        -
        resolved
    )

    print()

    print(
        "========================================"
    )

    print(
        "       CONSTELLATION DATA COMPLETE"
    )

    print(
        "========================================"
    )

    print(
        f"Constellation HIP stars: "
        f"{total:,}"
    )

    print(
        f"Gaia coordinates: "
        f"{gaia_count:,}"
    )

    print(
        f"SIMBAD coordinates: "
        f"{simbad_count:,}"
    )

    print(
        f"Total resolved: "
        f"{resolved:,}"
    )

    print(
        f"Unresolved: "
        f"{unresolved:,}"
    )

    if total:

        coverage = (
            resolved
            /
            total
            *
            100.0
        )

        print(
            f"Coverage: "
            f"{coverage:.2f}%"
        )

    print()

    print(
        "Saved:"
    )

    print(
        f"  {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()