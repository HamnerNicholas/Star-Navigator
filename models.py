import math

from dataclasses import dataclass


@dataclass
class Star:
    """
    Represents a single stellar system from the Gaia catalog.
    """

    source_id: int
    designation: str

    ra_deg: float
    dec_deg: float
    parallax_mas: float

    common_name: str | None

    magnitude: float | None = None
    bp_rp: float | None = None

    pmra: float | None = None
    pmdec: float | None = None
    radial_velocity: float | None = None

    # ========================================================
    # DISPLAY NAME
    # ========================================================

    @property
    def display_name(self):
        """
        Return the best available human-readable name
        for this star.
        """

        if self.common_name is not None:
            return self.common_name

        return self.designation

    # ========================================================
    # DISTANCE
    # ========================================================

    @property
    def distance_pc(self):
        """
        Distance from the Sun in parsecs.

        Gaia parallax is provided in milliarcseconds.
        """

        if math.isinf(
            self.parallax_mas
        ):
            return 0.0

        return (
            1000.0
            /
            self.parallax_mas
        )

    @property
    def distance_ly(self):
        """
        Distance from the Sun in light-years.
        """

        return (
            self.distance_pc
            *
            3.26156
        )

    # ========================================================
    # CARTESIAN COORDINATES
    # ========================================================

    def xyz(self):
        """
        Convert RA, Dec, and distance into Cartesian
        XYZ coordinates in light-years.

        The resulting coordinate system is centered on Sol.
        """

        ra = math.radians(
            self.ra_deg
        )

        dec = math.radians(
            self.dec_deg
        )

        distance = self.distance_ly

        x = (
            distance
            *
            math.cos(dec)
            *
            math.cos(ra)
        )

        y = (
            distance
            *
            math.cos(dec)
            *
            math.sin(ra)
        )

        z = (
            distance
            *
            math.sin(dec)
        )

        return (
            x,
            y,
            z
        )