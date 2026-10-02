from dataclasses import dataclass
from uuid import uuid4


trait_type_list = {"boolean", "range"}

@dataclass
class Trait:

    id: str
    name: str
    probability: float

    trait_type: str = "boolean"

    minimum: int | None = None
    maximum: int | None = None

    # ========================================================
    # CREATE NEW TRAIT
    # ========================================================

    @classmethod
    def create(
        cls,
        name,
        probability,
        trait_type,
        minimum=None,
        maximum=None
    ):

        name = name.strip()

        if not name:

            raise ValueError(
                "Trait name cannot be empty."
            )

        probability = float(
            probability
        )

        if not 0.0 <= probability <= 1.0:

            raise ValueError(
                "Trait probability must "
                "be between 0.0 and 1.0."
            )

        trait_type = trait_type.strip().lower() 

        if trait_type not in trait_type_list:
             raise ValueError(
                f"Unknown trait type: "
                f"{trait_type}"
            )

        if trait_type == "range":

            if (
                minimum is None
                or maximum is None
            ):

                raise ValueError(
                    "Range traits require "
                    "a minimum and maximum."
                )

            minimum = int(
                minimum
            )

            maximum = int(
                maximum
            )

            if minimum > maximum:

                raise ValueError(
                    "Trait minimum cannot "
                    "be greater than maximum."
                )

        else:

            minimum = None
            maximum = None

        # ========================================================
        # CREATE TRAIT
        # ========================================================

        return cls(
            id=str(
                uuid4()
            ),
            name=name,
            probability=probability,
            trait_type=trait_type,
            minimum=minimum,
            maximum=maximum
        )

    # ========================================================
    # PROBABILITY AS PERCENTAGE
    # ========================================================

    @property
    def probability_percent(
        self
    ):

        return (
            self.probability
            * 100.0
        )

    # ========================================================
    # UPDATE PROBABILITY
    # ========================================================

    def set_probability(
        self,
        probability
    ):

        probability = float(
            probability
        )

        if not 0.0 <= probability <= 1.0:

            raise ValueError(
                "Trait probability must "
                "be between 0.0 and 1.0."
            )

        self.probability = (
            probability
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self
    ):

        return {
            "id": self.id,
            "name": self.name,
            "probability": self.probability,
            "trait_type": self.trait_type,
            "minimum": self.minimum,
            "maximum": self.maximum
        }

    # ========================================================
    # DESERIALIZATION
    # ========================================================

    @classmethod
    def from_dict(
        cls,
        data
    ):

        if "id" not in data:
            raise ValueError(
                "Trait is missing an id."
            )

        if "name" not in data:
            raise ValueError(
                "Trait is missing a name."
            )

        if "probability" not in data:
            raise ValueError(
                "Trait is missing a probability."
            )

        if "trait_type" not in data:
            raise ValueError(
                "Trait is missing a type."
            )

        trait_type = str(
            data["trait_type"]
        ).strip().lower()

        if trait_type not in trait_type_list:

            raise ValueError(
                f"Unknown trait type: "
                f"{trait_type}"
            )

        # --------------------------------------------------------
        # Range values
        # --------------------------------------------------------

        if trait_type == "range":

            if "minimum" not in data:

                raise ValueError(
                    "Range trait is missing "
                    "a minimum."
                )

            if "maximum" not in data:

                raise ValueError(
                    "Range trait is missing "
                    "a maximum."
                )

            minimum = int(
                data["minimum"]
            )

            maximum = int(
                data["maximum"]
            )

            if minimum > maximum:

                raise ValueError(
                    "Trait minimum cannot "
                    "be greater than maximum."
                )

        else:

            minimum = None
            maximum = None

        return cls(
            id=str(
                data["id"]
            ),

            name=str(
                data["name"]
            ).strip(),

            probability=float(
                data["probability"]
            ),

            trait_type=trait_type,

            minimum=minimum,

            maximum=maximum
        )
    