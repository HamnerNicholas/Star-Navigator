import csv
import math

from .models import Star


def load_star_names(filename):
    names = {}

    with open(
        filename,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            source_id = int(
                row["source_id"]
            )

            common_name = row[
                "common_name"
            ].strip()

            names[source_id] = common_name

    return names


def parse_optional_float(value):

    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    return float(value)


def load_gaia_catalog(
    filename,
    star_names
):

    stars = []

    with open(
        filename,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            source_id = int(
                row["source_id"]
            )

            star = Star(
                source_id=source_id,

                designation=row[
                    "designation"
                ],

                ra_deg=float(
                    row["ra"]
                ),

                dec_deg=float(
                    row["dec"]
                ),

                parallax_mas=float(
                    row["parallax"]
                ),

                common_name=star_names.get(
                    source_id
                ),

                magnitude=parse_optional_float(
                    row["phot_g_mean_mag"]
                ),

                bp_rp=parse_optional_float(
                    row["bp_rp"]
                ),

                pmra=parse_optional_float(
                    row["pmra"]
                ),

                pmdec=parse_optional_float(
                    row["pmdec"]
                ),

                radial_velocity=parse_optional_float(
                    row["radial_velocity"]
                )
            )

            stars.append(
                star
            )

    print(
        f"Loaded {len(stars):,} Gaia stars."
    )

    return stars


def add_sol(stars):

    sol = Star(
        source_id=0,

        designation="Sol",

        ra_deg=0.0,
        dec_deg=0.0,

        parallax_mas=float(
            "inf"
        ),

        common_name=None,

        magnitude=-26.74,

        bp_rp=None,

        pmra=None,
        pmdec=None,
        radial_velocity=None
    )

    stars.insert(
        0,
        sol
    )