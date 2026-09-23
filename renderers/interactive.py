import math

import plotly.graph_objects as go

from .colors import gaia_color_to_rgb

from ..config import MAX_JUMP_DISTANCE

from .constellations import (
    load_constellation_stars,
    load_constellation_definitions,
    build_constellation_lines,
    build_constellation_labels,
)

from ..config import (
    MAX_JUMP_DISTANCE,
    CONSTELLATION_LINES_FILE,
    CONSTELLATION_GAIA_FILE,
)



def draw_interactive_map(
    graph,
    stars,
    route,
    filename="interactive_star_map.html",
    background_radius=70.0,
    show_constellations=False,
    show_constellation_names=False,
):
    """
    Render an interactive 3D navigation map using Plotly.

    Features:
    - true 3D stellar positions
    - interactive rotation and zoom
    - Gaia-derived stellar colors
    - configurable background-star radius around route
    - background star brightness/size attenuation
    - hover information for stars and jumps
    - hidden axes for a cleaner space-style presentation
    """

    # ========================================================
    # ROUTE DATA
    # ========================================================

    route_stars = [
        graph.nodes[source_id]["star"]
        for source_id in route
    ]

    route_ids = set(route)

    route_positions = [
        star.xyz()
        for star in route_stars
    ]

    # ========================================================
    # CREATE FIGURE
    # ========================================================

    fig = go.Figure()

    # ========================================================
    # BACKGROUND STAR DATA
    # ========================================================

    background_x = []
    background_y = []
    background_z = []

    background_sizes = []
    background_colors = []
    background_hover = []

    for star in stars:

        if star.source_id in route_ids:
            continue

        x, y, z = star.xyz()

        # ----------------------------------------------------
        # FIND DISTANCE TO NEAREST ROUTE STAR
        # ----------------------------------------------------

        min_route_distance = float("inf")

        for route_x, route_y, route_z in route_positions:

            dx = x - route_x
            dy = y - route_y
            dz = z - route_z

            distance = math.sqrt(
                dx * dx
                + dy * dy
                + dz * dz
            )

            if distance < min_route_distance:
                min_route_distance = distance

        # Ignore stars outside the selected neighborhood
        if min_route_distance > background_radius:
            continue

        # ----------------------------------------------------
        # STORE POSITION
        # ----------------------------------------------------

        background_x.append(x)
        background_y.append(y)
        background_z.append(z)

        # ----------------------------------------------------
        # SIZE FROM MAGNITUDE
        # ----------------------------------------------------

        if star.magnitude is None:
            base_size = 2.5

        else:
            base_size = max(
                1.5,
                min(
                    7.0,
                    7.0 - star.magnitude * 0.28
                )
            )

        # ----------------------------------------------------
        # DISTANCE ATTENUATION
        # ----------------------------------------------------

        distance_factor = max(
            0.20,
            1.0
            - (
                min_route_distance
                / background_radius
            )
        )

        size = (
            base_size
            * (
                0.45
                + 0.55 * distance_factor
            )
        )

        background_sizes.append(
            size
        )

        # ----------------------------------------------------
        # GAIA COLOR
        # ----------------------------------------------------

        background_colors.append(
            gaia_color_to_rgb(
                star.bp_rp
            )
        )

        # ----------------------------------------------------
        # HOVER INFORMATION
        # ----------------------------------------------------

        hover_text = (
            f"<b>{star.display_name}</b>"
            f"<br>"
            f"Distance from Sol: "
            f"{star.distance_ly:.2f} ly"
        )

        if star.magnitude is not None:

            hover_text += (
                f"<br>"
                f"G Magnitude: "
                f"{star.magnitude:.2f}"
            )

        if star.bp_rp is not None:

            hover_text += (
                f"<br>"
                f"BP-RP: "
                f"{star.bp_rp:.2f}"
            )

        hover_text += (
            f"<br>"
            f"Gaia ID: "
            f"{star.source_id}"
        )

        background_hover.append(
            hover_text
        )

    # ========================================================
    # DRAW BACKGROUND STARS
    # ========================================================

    fig.add_trace(
        go.Scatter3d(

            x=background_x,
            y=background_y,
            z=background_z,

            mode="markers",

            marker=dict(

                size=background_sizes,

                color=background_colors,

                opacity=0.50
            ),

            hovertext=background_hover,

            hovertemplate=(
                "%{hovertext}"
                "<extra></extra>"
            ),

            name="Catalog Stars"
        )
    )

    # ========================================================
    # CONSTELLATIONS
    # ========================================================

    if show_constellations:

        constellation_stars = (
            load_constellation_stars(
                CONSTELLATION_GAIA_FILE
            )
        )

        constellation_data = (
            load_constellation_definitions(
                CONSTELLATION_LINES_FILE
            )
        )

        constellation_radius = max(
            background_radius + 100.0,
            200.0
        )

        (
            constellation_traces,
            constellation_segments,
            skipped_segments
        ) = build_constellation_lines(
            constellation_stars,
            constellation_data,
            constellation_radius
        )

        for constellation in (
            constellation_traces
        ):

            fig.add_trace(
                go.Scatter3d(

                    x=constellation["x"],
                    y=constellation["y"],
                    z=constellation["z"],

                    mode="lines",

                    line=dict(
                        color=(
                            "rgba(120, "
                            "190, "
                            "255, "
                            "0.65)"
                        ),
                        width=2
                    ),

                    hoverinfo="skip",

                    showlegend=False
                )
            )

        print(
            f"Constellation segments: "
            f"{constellation_segments:,}"
        )

        print(
            f"Skipped constellation segments: "
            f"{skipped_segments:,}"
        )

    # ========================================================
    # CONSTELLATION NAMES
    # ========================================================

    if show_constellation_names:

        constellation_labels = (
            build_constellation_labels(
                constellation_stars,
                constellation_data,
                constellation_radius
            )
        )

        fig.add_trace(
            go.Scatter3d(

                x=[
                    label["x"]
                    for label
                    in constellation_labels
                ],

                y=[
                    label["y"]
                    for label
                    in constellation_labels
                ],

                z=[
                    label["z"]
                    for label
                    in constellation_labels
                ],

                mode="text",

                text=[
                    label["name"]
                    for label
                    in constellation_labels
                ],

                textfont=dict(
                    color="rgba(190, 220, 255, 0.85)",
                    size=11
                ),

                hoverinfo="skip",

                showlegend=False
            )
        )

    # ========================================================
    # ROUTE LINE DATA
    # ========================================================

    line_x = []
    line_y = []
    line_z = []

    jump_hover_x = []
    jump_hover_y = []
    jump_hover_z = []

    jump_hover_text = []

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

        ax_x, ax_y, ax_z = (
            star_a.xyz()
        )

        bx_x, bx_y, bx_z = (
            star_b.xyz()
        )

        distance = graph[
            route[i]
        ][
            route[i + 1]
        ]["distance"]

        total_distance += distance

        # ----------------------------------------------------
        # ROUTE SEGMENT
        # ----------------------------------------------------

        line_x.extend([
            ax_x,
            bx_x,
            None
        ])

        line_y.extend([
            ax_y,
            bx_y,
            None
        ])

        line_z.extend([
            ax_z,
            bx_z,
            None
        ])

        # ----------------------------------------------------
        # INVISIBLE MIDPOINT FOR HOVER
        # ----------------------------------------------------

        midpoint_x = (
            ax_x + bx_x
        ) / 2

        midpoint_y = (
            ax_y + bx_y
        ) / 2

        midpoint_z = (
            ax_z + bx_z
        ) / 2

        jump_hover_x.append(
            midpoint_x
        )

        jump_hover_y.append(
            midpoint_y
        )

        jump_hover_z.append(
            midpoint_z
        )

        jump_hover_text.append(
            f"<b>{star_a.display_name}</b>"
            f" → "
            f"<b>{star_b.display_name}</b>"
            f"<br>"
            f"Jump Distance: "
            f"{distance:.2f} ly"
        )

    # ========================================================
    # DRAW ROUTE
    # ========================================================

    fig.add_trace(
        go.Scatter3d(

            x=line_x,
            y=line_y,
            z=line_z,

            mode="lines",

            line=dict(
                color="cyan",
                width=6
            ),

            hoverinfo="skip",

            name="Route"
        )
    )

    # ========================================================
    # JUMP HOVER MARKERS
    # ========================================================

    fig.add_trace(
        go.Scatter3d(

            x=jump_hover_x,
            y=jump_hover_y,
            z=jump_hover_z,

            mode="markers",

            marker=dict(
                size=10,
                color="rgba(0,0,0,0)"
            ),

            hovertext=jump_hover_text,

            hovertemplate=(
                "%{hovertext}"
                "<extra></extra>"
            ),

            showlegend=False
        )
    )

    # ========================================================
    # ROUTE STARS
    # ========================================================

    route_marker_x = []
    route_marker_y = []
    route_marker_z = []

    route_colors = []
    route_sizes = []
    route_hover = []

    for i, star in enumerate(
        route_stars
    ):

        x, y, z = star.xyz()

        route_marker_x.append(x)
        route_marker_y.append(y)
        route_marker_z.append(z)

        # ----------------------------------------------------
        # ROLE
        # ----------------------------------------------------

        if i == 0:

            marker_color = "gold"
            marker_size = 11
            role = "Starting System"

        elif i == len(route_stars) - 1:

            marker_color = "red"
            marker_size = 11
            role = "Destination"

        else:

            marker_color = "cyan"
            marker_size = 8
            role = f"Route Stop {i}"

        route_colors.append(
            marker_color
        )

        route_sizes.append(
            marker_size
        )

        # ----------------------------------------------------
        # HOVER INFO
        # ----------------------------------------------------

        hover_text = (
            f"<b>{star.display_name}</b>"
            f"<br>"
            f"{role}"
            f"<br><br>"
            f"Distance from Sol: "
            f"{star.distance_ly:.2f} ly"
        )

        if star.magnitude is not None:

            hover_text += (
                f"<br>"
                f"G Magnitude: "
                f"{star.magnitude:.2f}"
            )

        if star.bp_rp is not None:

            hover_text += (
                f"<br>"
                f"BP-RP: "
                f"{star.bp_rp:.2f}"
            )

        hover_text += (
            f"<br>"
            f"Gaia ID: "
            f"{star.source_id}"
        )

        # ----------------------------------------------------
        # NEXT JUMP
        # ----------------------------------------------------

        if i < len(route_stars) - 1:

            next_id = (
                route[i + 1]
            )

            next_star = graph.nodes[
                next_id
            ]["star"]

            jump_distance = graph[
                star.source_id
            ][
                next_id
            ]["distance"]

            hover_text += (
                f"<br><br>"
                f"<b>Next:</b> "
                f"{next_star.display_name}"
                f"<br>"
                f"<b>Jump:</b> "
                f"{jump_distance:.2f} ly"
            )

        route_hover.append(
            hover_text
        )

    # ========================================================
    # DRAW ROUTE STARS
    # ========================================================

    fig.add_trace(
        go.Scatter3d(

            x=route_marker_x,
            y=route_marker_y,
            z=route_marker_z,

            mode="markers",

            marker=dict(

                size=route_sizes,

                color=route_colors,

                line=dict(
                    color="white",
                    width=1
                )
            ),

            hovertext=route_hover,

            hovertemplate=(
                "%{hovertext}"
                "<extra></extra>"
            ),

            name="Route Systems"
        )
    )

    # ========================================================
    # SELECTED SYSTEM HIGHLIGHT
    # ========================================================

    selected_x, selected_y, selected_z = (
        route_stars[0].xyz()
    )

    fig.add_trace(
        go.Scatter3d(

            x=[selected_x],
            y=[selected_y],
            z=[selected_z],

            mode="markers",

            marker=dict(
                size=10,
                color="magenta",
                opacity=1.0,

                line=dict(
                    color="purple",
                    width=3
                )
            ),

            hoverinfo="skip",

            name="Selected System",

            showlegend=False
        )
    )
    # ========================================================
    # TITLE
    # ========================================================

    start_star = (
        route_stars[0]
    )

    destination_star = (
        route_stars[-1]
    )

    title = (
        f"{start_star.display_name}"
        f" → "
        f"{destination_star.display_name}"
        f"<br>"
        f"<sup>"
        f"{len(route) - 1} jumps"
        f" | "
        f"{total_distance:.2f} light-years"
        f" | "
        f"Maximum jump: "
        f"{MAX_JUMP_DISTANCE:.1f} ly"
        f" | "
        f"Visible radius: "
        f"{background_radius:.0f} ly"
        f"</sup>"
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(

        title=dict(
            text=title,
            x=0.5,
            xanchor="center"
        ),

        paper_bgcolor="black",
        plot_bgcolor="black",

        font=dict(
            color="white"
        ),

        hoverlabel=dict(
            bgcolor="#101923",
            bordercolor="#00d9ff",
            font=dict(
                color="#edf5ff",
                size=12
            )
        ),

        legend=dict(

            bgcolor=(
                "rgba(0,0,0,0.5)"
            ),

            x=0.01,
            y=0.99
        ),

        scene=dict(

            bgcolor="black",

            # Hide all axes/grid lines
            xaxis=dict(
                visible=False
            ),

            yaxis=dict(
                visible=False
            ),

            zaxis=dict(
                visible=False
            ),

            # Normalized display for easier 3D exploration
            aspectmode="cube",

            camera=dict(
                eye=dict(
                    x=1.0,
                    y=1.0,
                    z=0.8
                )
            )
        ),

        margin=dict(
            l=0,
            r=0,
            b=0,
            t=80
        )
        
    )

    # ========================================================
    # SAVE INTERACTIVE HTML
    # ========================================================

    fig.write_html(
        filename,
        include_plotlyjs=True,
        full_html=True,
        div_id="starNavigatorPlot"
    )

    print(
        f"\nInteractive map saved as: "
        f"{filename}"
    )

    print(
        f"Rendered "
        f"{len(background_x):,} "
        f"background stars."
    )

    return fig