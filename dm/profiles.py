import json
from pathlib import Path

from .traits import Trait


PROFILE_VERSION = 1


# ============================================================
# SAVE PROFILE
# ============================================================

def save_profile(
    filename,
    traits
):
    """
    Save a DM trait profile to a JSON file.

    Only the trait definitions are stored.
    Generated route results are intentionally not stored.
    """

    path = Path(
        filename
    )

    data = {
        "version": PROFILE_VERSION,

        "traits": [
            trait.to_dict()
            for trait in traits
        ]
    }

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


# ============================================================
# LOAD PROFILE
# ============================================================

def load_profile(
    filename
):
    """
    Load a DM trait profile from a JSON file.

    Returns:
        list[Trait]
    """

    path = Path(
        filename
    )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(
            file
        )

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            "Invalid DM profile format."
        )

    version = data.get(
        "version"
    )

    if version != PROFILE_VERSION:

        raise ValueError(
            f"Unsupported DM profile version: "
            f"{version}"
        )

    trait_data = data.get(
        "traits"
    )

    if not isinstance(
        trait_data,
        list
    ):

        raise ValueError(
            "DM profile is missing "
            "a valid traits list."
        )

    traits = []

    for entry in trait_data:

        if not isinstance(
            entry,
            dict
        ):

            raise ValueError(
                "Invalid trait entry "
                "in DM profile."
            )

        traits.append(
            Trait.from_dict(
                entry
            )
        )

    return traits