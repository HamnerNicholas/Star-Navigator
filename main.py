import networkx as nx

from .config import (
    CATALOG_FILE,
    STAR_NAME_FILE,
    MAX_JUMP_DISTANCE,
    BACKGROUND_RADIUS,
    INTERACTIVE_MAP_FILE,
)

from .catalog import (
    load_star_names,
    load_gaia_catalog,
    add_sol,
)

from .navigation.graph import (
    build_navigation_graph,
    print_graph_info,
)

from .navigation.routing import (
    build_star_lookup,
    find_star,
    find_route,
    print_route,
)

from .renderers.interactive import (
    draw_interactive_map,
)


def main():

    # ========================================================
    # LOAD STAR NAME CATALOG
    # ========================================================

    print(
        f"Loading star names: "
        f"{STAR_NAME_FILE}"
    )

    star_names = load_star_names(
        STAR_NAME_FILE
    )

    print(
        f"Loaded "
        f"{len(star_names):,} star names."
    )

    # ========================================================
    # LOAD GAIA CATALOG
    # ========================================================

    stars = load_gaia_catalog(
        CATALOG_FILE,
        star_names
    )

    # Sol is added manually because it is not loaded through
    # the same Gaia catalog path as the other stars.

    add_sol(
        stars
    )

    # ========================================================
    # BUILD NAVIGATION GRAPH
    # ========================================================

    graph = build_navigation_graph(
        stars,
        MAX_JUMP_DISTANCE
    )

    print_graph_info(
        graph
    )

    # ========================================================
    # BUILD STAR LOOKUP
    # ========================================================

    lookup = build_star_lookup(
        stars
    )

    # ========================================================
    # USER INPUT
    # ========================================================

    print()
    print(
        "========================================"
    )
    print(
        "        INTERSTELLAR NAVIGATION"
    )
    print(
        "========================================"
    )
    print()

    start_name = input(
        "Enter starting system: "
    ).strip()

    destination_name = input(
        "Enter destination: "
    ).strip()

    # ========================================================
    # FIND STARTING SYSTEM
    # ========================================================

    start = find_star(
        lookup,
        start_name
    )

    if start is None:

        print()
        print(
            f"Could not find star: "
            f"{start_name}"
        )

        return

    # ========================================================
    # FIND DESTINATION SYSTEM
    # ========================================================

    destination = find_star(
        lookup,
        destination_name
    )

    if destination is None:

        print()
        print(
            f"Could not find star: "
            f"{destination_name}"
        )

        return

    print()
    print(
        f"Starting system: "
        f"{start.display_name}"
    )

    print(
        f"Destination: "
        f"{destination.display_name}"
    )

    # ========================================================
    # FIND ROUTES
    # ========================================================

    try:

        shortest_route = find_route(
            graph,
            start.source_id,
            destination.source_id,
            mode="shortest_distance"
        )

        fewest_jump_route = find_route(
            graph,
            start.source_id,
            destination.source_id,
            mode="fewest_jumps"
        )

    except nx.NetworkXNoPath:

        print()
        print(
            f"No route exists from "
            f"{start.display_name} "
            f"to "
            f"{destination.display_name} "
            f"with a "
            f"{MAX_JUMP_DISTANCE:.1f} ly "
            f"jump range."
        )

        return

    # ========================================================
    # PRINT SHORTEST DISTANCE ROUTE
    # ========================================================

    print()
    print(
        "===== SHORTEST DISTANCE ====="
    )

    print_route(
        graph,
        shortest_route
    )

    # ========================================================
    # PRINT FEWEST JUMPS ROUTE
    # ========================================================

    print()
    print(
        "===== FEWEST JUMPS ====="
    )

    print_route(
        graph,
        fewest_jump_route
    )

    # ========================================================
    # GENERATE INTERACTIVE MAP
    # ========================================================

    print()
    print(
        "Generating interactive map..."
    )

    fig = draw_interactive_map(
        graph,
        stars,
        shortest_route,
        filename=INTERACTIVE_MAP_FILE,
        background_radius=BACKGROUND_RADIUS
    )

    # ========================================================
    # DISPLAY INTERACTIVE MAP
    # ========================================================

    fig.show()


if __name__ == "__main__":
    main()