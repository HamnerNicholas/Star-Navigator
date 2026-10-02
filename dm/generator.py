import hashlib

from .traits import Trait


# ============================================================
# DETERMINISTIC ROLL
# ============================================================

def trait_roll(
    source_id,
    trait_id,
    purpose
):
    """
    Generate a deterministic pseudo-random value between
    0.0 and 1.0 for a specific star, trait, and purpose.

    The same inputs will always produce the same value.

    Examples of purpose:
        "exists"
        "value"
    """

    seed = (
        f"{source_id}:"
        f"{trait_id}:"
        f"{purpose}"
    )

    digest = hashlib.sha256(
        seed.encode(
            "utf-8"
        )
    ).digest()

    value = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False
    )

    return (
        value
        / (2**64 - 1)
    )


# ============================================================
# TRAIT EXISTENCE
# ============================================================

def trait_exists(
    source_id,
    trait
):
    """
    Determine whether a procedural trait exists for a star.

    Returns False for Sol (source_id == 0).

    The existence decision uses only the existence roll, so
    changing the trait probability does not change its
    underlying generated value.
    """

    if source_id == 0:

        return False

    roll = trait_roll(
        source_id,
        trait.id,
        "exists"
    )

    return (
        roll
        < trait.probability
    )


# ============================================================
# TRAIT VALUE
# ============================================================

def generate_trait_value(
    source_id,
    trait
):
    """
    Generate the deterministic value for an existing trait.

    Boolean traits return True.

    Range traits return an integer between minimum and
    maximum, inclusive.

    The value is generated independently of the existence
    probability.
    """

    if trait.trait_type == "boolean":

        return True

    if trait.trait_type == "range":

        if (
            trait.minimum is None
            or trait.maximum is None
        ):

            raise ValueError(
                f"Range trait '{trait.name}' "
                f"requires minimum and maximum."
            )

        roll = trait_roll(
            source_id,
            trait.id,
            "value"
        )

        value_range = (
            trait.maximum
            -
            trait.minimum
            +
            1
        )

        return (
            trait.minimum
            +
            int(
                roll
                * value_range
            )
        )

    raise ValueError(
        f"Unknown trait type: "
        f"{trait.trait_type}"
    )


# ============================================================
# GENERATE ONE TRAIT
# ============================================================

def generate_trait(
    source_id,
    trait
):
    """
    Generate one trait for a star.

    Returns:

        None
            if the trait does not occur.

        True
            for an existing boolean trait.

        integer
            for an existing range trait.

    Sol always returns None.
    """

    if source_id == 0:

        return None

    if not trait_exists(
        source_id,
        trait
    ):

        return None

    return generate_trait_value(
        source_id,
        trait
    )


# ============================================================
# GENERATE ALL TRAITS FOR ONE STAR
# ============================================================

def generate_star_traits(
    source_id,
    traits
):
    """
    Generate all procedural traits for one star.

    Returns a dictionary:

        {
            trait_id: generated_value
        }

    Only traits that actually occur are included.

    Sol returns an empty dictionary.
    """

    if source_id == 0:

        return {}

    results = {}

    for trait in traits:

        value = generate_trait(
            source_id,
            trait
        )

        if value is not None:

            results[
                trait.id
            ] = value

    return results


# ============================================================
# GENERATE ALL TRAITS FOR A ROUTE
# ============================================================

def generate_route_traits(
    route,
    traits
):
    """
    Generate procedural traits for every system in a route.

    Returns:

        {
            source_id: {
                trait_id: generated_value
            }
        }

    Sol is included with an empty dictionary.
    """

    results = {}

    for source_id in route:

        results[source_id] = (
            generate_star_traits(
                source_id,
                traits
            )
        )

    return results