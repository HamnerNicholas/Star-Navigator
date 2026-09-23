import csv
import json
import math


# ============================================================
# LOAD CONSTELLATION STAR COORDINATES
# ============================================================

def load_constellation_stars(
    filename
):

    stars = {}

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

            hip_id = int(
                row["hip_id"]
            )

            stars[
                hip_id
            ] = {
                "ra_deg": float(
                    row["ra_deg"]
                ),

                "dec_deg": float(
                    row["dec_deg"]
                ),

                "gaia_source_id": (
                    int(
                        row["gaia_source_id"]
                    )
                    if row["gaia_source_id"]
                    else None
                ),

                "source": row[
                    "source"
                ]
            }

    return stars


# ============================================================
# LOAD CONSTELLATION DEFINITIONS
# ============================================================

def load_constellation_definitions(
    filename
):

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


# ============================================================
# SKY COORDINATES
# ============================================================

def sky_direction(
    ra_deg,
    dec_deg,
    radius
):

    ra = math.radians(
        ra_deg
    )

    dec = math.radians(
        dec_deg
    )

    x = (
        radius
        * math.cos(dec)
        * math.cos(ra)
    )

    y = (
        radius
        * math.cos(dec)
        * math.sin(ra)
    )

    z = (
        radius
        * math.sin(dec)
    )

    return (
        x,
        y,
        z
    )


# ============================================================
# BUILD CONSTELLATION LINE TRACES
# ============================================================

def build_constellation_lines(
    constellation_stars,
    constellation_data,
    radius
):

    traces = []

    total_segments = 0
    skipped_segments = 0

    # --------------------------------------------------------
    # Process every constellation
    # --------------------------------------------------------

    for constellation in (
        constellation_data[
            "constellations"
        ]
    ):

        iau = constellation.get(
            "iau"
        )

        lines = constellation.get(
            "lines",
            []
        )

        line_x = []
        line_y = []
        line_z = []

        # ----------------------------------------------------
        # Process line definitions
        # ----------------------------------------------------

        for line in lines:

            hip_ids = [
                value
                for value in line
                if isinstance(
                    value,
                    int
                )
            ]

            if len(hip_ids) < 2:

                continue

            # ------------------------------------------------
            # Draw EACH consecutive pair
            # ------------------------------------------------

            for i in range(
                len(hip_ids) - 1
            ):

                hip_a = hip_ids[i]
                hip_b = hip_ids[i + 1]

                star_a = (
                    constellation_stars.get(
                        hip_a
                    )
                )

                star_b = (
                    constellation_stars.get(
                        hip_b
                    )
                )

                # --------------------------------------------
                # Missing coordinate
                # --------------------------------------------

                if (
                    star_a is None
                    or
                    star_b is None
                ):

                    skipped_segments += 1

                    continue

                # --------------------------------------------
                # Coordinates
                # --------------------------------------------

                ax, ay, az = (
                    sky_direction(
                        star_a["ra_deg"],
                        star_a["dec_deg"],
                        radius
                    )
                )

                bx, by, bz = (
                    sky_direction(
                        star_b["ra_deg"],
                        star_b["dec_deg"],
                        radius
                    )
                )

                line_x.extend([
                    ax,
                    bx,
                    None
                ])

                line_y.extend([
                    ay,
                    by,
                    None
                ])

                line_z.extend([
                    az,
                    bz,
                    None
                ])

                total_segments += 1

        # ----------------------------------------------------
        # Add constellation trace
        # ----------------------------------------------------

        if not line_x:

            continue

        traces.append({
            "iau": iau,
            "x": line_x,
            "y": line_y,
            "z": line_z
        })

    return (
        traces,
        total_segments,
        skipped_segments
    )