def gaia_color_to_rgb(
    bp_rp
):
    """
    Convert Gaia BP-RP color index to an approximate
    display RGB color using continuous interpolation.

    This is intended for visualization, not precision
    photometry.
    """

    if bp_rp is None:
        return "rgb(255, 255, 255)"

    # --------------------------------------------------------
    # COLOR ANCHORS
    # --------------------------------------------------------

    color_stops = [
        (-0.5, (155, 176, 255)),
        ( 0.0, (180, 200, 255)),
        ( 0.5, (220, 230, 255)),
        ( 1.0, (255, 250, 230)),
        ( 1.5, (255, 220, 170)),
        ( 2.0, (255, 190, 130)),
        ( 3.0, (255, 140, 100)),
        ( 4.0, (255, 100, 80)),
    ]

    # --------------------------------------------------------
    # CLAMP VALUE
    # --------------------------------------------------------

    bp_rp = max(
        color_stops[0][0],
        min(
            color_stops[-1][0],
            bp_rp
        )
    )

    # --------------------------------------------------------
    # FIND SURROUNDING COLOR STOPS
    # --------------------------------------------------------

    for i in range(
        len(color_stops) - 1
    ):

        value_a, color_a = (
            color_stops[i]
        )

        value_b, color_b = (
            color_stops[i + 1]
        )

        if value_a <= bp_rp <= value_b:

            t = (
                (bp_rp - value_a)
                /
                (value_b - value_a)
            )

            red = round(
                color_a[0]
                +
                (
                    color_b[0]
                    -
                    color_a[0]
                )
                * t
            )

            green = round(
                color_a[1]
                +
                (
                    color_b[1]
                    -
                    color_a[1]
                )
                * t
            )

            blue = round(
                color_a[2]
                +
                (
                    color_b[2]
                    -
                    color_a[2]
                )
                * t
            )

            return (
                f"rgb("
                f"{red}, "
                f"{green}, "
                f"{blue}"
                f")"
            )

    return "rgb(255, 255, 255)"