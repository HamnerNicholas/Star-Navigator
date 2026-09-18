import math

import matplotlib.pyplot as plt

from ..config import MAX_JUMP_DISTANCE

def draw_static_map(
    graph,
    stars,
    route,
    filename="star_route_3d.png"
):
    """
    Render the navigation route in true 3D Cartesian space.

    All star positions use their real XYZ coordinates relative
    to Sol, measured in light-years.

    The route calculation and the visualization therefore use
    the same spatial geometry.
    """

    # ========================================================
    # GET ROUTE STARS
    # ========================================================

    route_stars = [
        graph.nodes[source_id]["star"]
        for source_id in route
    ]

    route_ids = set(route)

    # ========================================================
    # CREATE 3D FIGURE
    # ========================================================

    fig = plt.figure(
        figsize=(14, 10)
    )

    fig.patch.set_facecolor(
        "black"
    )

    ax = fig.add_subplot(
        111,
        projection="3d"
    )

    ax.set_facecolor(
        "black"
    )

    # ========================================================
    # ROUTE BOUNDS
    # ========================================================

    route_x = []
    route_y = []
    route_z = []

    for star in route_stars:

        x, y, z = star.xyz()

        route_x.append(x)
        route_y.append(y)
        route_z.append(z)

    min_x = min(route_x)
    max_x = max(route_x)

    min_y = min(route_y)
    max_y = max(route_y)

    min_z = min(route_z)
    max_z = max(route_z)

    width_x = max_x - min_x
    width_y = max_y - min_y
    width_z = max_z - min_z

    padding_x = max(width_x * 1.00, 25)
    padding_y = max(width_y * 1.00, 25)
    padding_z = max(width_z * 1.00, 25)

    view_min_x = min_x - padding_x
    view_max_x = max_x + padding_x

    view_min_y = min_y - padding_y
    view_max_y = max_y + padding_y

    view_min_z = min_z - padding_z
    view_max_z = max_z + padding_z

    # ========================================================
    # DRAW BACKGROUND STARS
    # ========================================================

    background_x = []
    background_y = []
    background_z = []
    background_sizes = []

    BACKGROUND_RADIUS = 20.0

    route_positions = [
        star.xyz()
        for star in route_stars
    ]

    for star in stars:

        if star.source_id in route_ids:
            continue

        x, y, z = star.xyz()

        show_star = False

        for route_x, route_y, route_z in route_positions:

            dx = x - route_x
            dy = y - route_y
            dz = z - route_z

            distance = math.sqrt(
                dx * dx +
                dy * dy +
                dz * dz
            )

            if distance <= BACKGROUND_RADIUS:
                show_star = True
                break

        if not show_star:
            continue

        background_x.append(x)
        background_y.append(y)
        background_z.append(z)

        if star.magnitude is None:

            size = 2

        else:

            size = max(
                1,
                min(
                    18,
                    14 - star.magnitude
                )
            )

        background_sizes.append(
            size
        )

    ax.scatter(
        background_x,
        background_y,
        background_z,

        s=background_sizes,

        color="white",

        alpha=0.18,

        linewidths=0,

        depthshade=True,

        zorder=1
    )

    # ========================================================
    # DRAW ROUTE CONNECTIONS
    # ========================================================

    total_distance = 0.0

    for i in range(
        len(route) - 1
    ):

        star_a = graph.nodes[
            route[i]
        ]["star"]

        star_b = graph.nodes[
            route[i + 1]
        ]["star"]

        ax_x, ax_y, ax_z = star_a.xyz()
        bx_x, bx_y, bx_z = star_b.xyz()

        distance = graph[
            route[i]
        ][
            route[i + 1]
        ]["distance"]

        total_distance += distance

        # -----------------------------------------------
        # Draw jump
        # -----------------------------------------------

        ax.plot(
            [ax_x, bx_x],
            [ax_y, bx_y],
            [ax_z, bx_z],

            color="cyan",

            linewidth=2.5,

            zorder=5
        )

        # -----------------------------------------------
        # Distance label at 3D midpoint
        # -----------------------------------------------

        midpoint_x = (
            ax_x + bx_x
        ) / 2

        midpoint_y = (
            ax_y + bx_y
        ) / 2

        midpoint_z = (
            ax_z + bx_z
        ) / 2

        ax.text(
            midpoint_x,
            midpoint_y,
            midpoint_z,

            f"{distance:.2f} ly",

            fontsize=8,

            color="white",

            ha="center",
            va="center",

            zorder=8
        )

    # ========================================================
    # DRAW ROUTE SYSTEMS
    # ========================================================

    for i, star in enumerate(
        route_stars
    ):

        x, y, z = star.xyz()

        if i == 0:

            marker_size = 150
            marker_color = "gold"

            label = (
                f"START\n"
                f"{star.display_name}"
            )

        elif i == len(route_stars) - 1:

            marker_size = 150
            marker_color = "red"

            label = (
                f"DESTINATION\n"
                f"{star.display_name}"
            )

        else:

            marker_size = 80
            marker_color = "cyan"

            label = star.display_name

        ax.scatter(
            [x],
            [y],
            [z],

            s=marker_size,

            color=marker_color,

            edgecolors="white",

            linewidths=1.0,

            depthshade=False,

            zorder=7
        )

        ax.text(
            x,
            y,
            z + 0.7,

            label,

            fontsize=9,

            color="white",

            ha="center",

            zorder=9
        )

    # ========================================================
    # TITLE
    # ========================================================

    start_star = route_stars[0]
    destination_star = route_stars[-1]

    title = (
        f"{start_star.display_name}"
        f" → "
        f"{destination_star.display_name}"
    )

    subtitle = (
        f"{len(route) - 1} jumps"
        f"   |   "
        f"{total_distance:.2f} light-years"
        f"   |   "
        f"Maximum jump: "
        f"{MAX_JUMP_DISTANCE:.1f} ly"
    )

    ax.set_title(
        title + "\n" + subtitle,

        fontsize=16,

        color="white",

        pad=20
    )

    # ========================================================
    # AXIS LIMITS
    # ========================================================

    ax.set_xlim(
        view_min_x,
        view_max_x
    )

    ax.set_ylim(
        view_min_y,
        view_max_y
    )

    ax.set_zlim(
        view_min_z,
        view_max_z
    )

    # ========================================================
    # AXIS LABELS
    # ========================================================

    ax.set_xlabel(
        "X Position (light-years)",
        color="white",
        labelpad=10
    )

    ax.set_ylabel(
        "Y Position (light-years)",
        color="white",
        labelpad=10
    )

    ax.set_zlabel(
        "Z Position (light-years)",
        color="white",
        labelpad=10
    )

    ax.tick_params(
        colors="white"
    )

    # ========================================================
    # DARK 3D PANES
    # ========================================================

    ax.xaxis.pane.set_facecolor(
        (0, 0, 0, 1)
    )

    ax.yaxis.pane.set_facecolor(
        (0, 0, 0, 1)
    )

    ax.zaxis.pane.set_facecolor(
        (0, 0, 0, 1)
    )

    ax.xaxis.pane.set_edgecolor(
        (1, 1, 1, 0.15)
    )

    ax.yaxis.pane.set_edgecolor(
        (1, 1, 1, 0.15)
    )

    ax.zaxis.pane.set_edgecolor(
        (1, 1, 1, 0.15)
    )

    # ========================================================
    # GRID STYLING
    # ========================================================

    ax.grid(
        True
    )

    ax.xaxis._axinfo["grid"]["color"] = (
        1,
        1,
        1,
        0.08
    )

    ax.yaxis._axinfo["grid"]["color"] = (
        1,
        1,
        1,
        0.08
    )

    ax.zaxis._axinfo["grid"]["color"] = (
        1,
        1,
        1,
        0.08
    )

    # ========================================================
    # INITIAL CAMERA ANGLE
    # ========================================================

    ax.view_init(
        elev=25,
        azim=-60
    )

    # ========================================================
    # SAVE
    # ========================================================

    plt.tight_layout()

    plt.savefig(
        filename,

        dpi=300,

        bbox_inches="tight",

        facecolor=fig.get_facecolor()
    )

    print(
        f"\n3D map saved as: {filename}"
    )

    return fig