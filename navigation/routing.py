import networkx as nx


def find_route(
    graph,
    start_id,
    destination_id,
    mode="shortest_distance"
):

    if mode == "shortest_distance":

        return nx.shortest_path(
            graph,
            source=start_id,
            target=destination_id,
            weight="distance"
        )

    elif mode == "fewest_jumps":

        return nx.shortest_path(
            graph,
            source=start_id,
            target=destination_id
        )

    else:

        raise ValueError(
            f"Unknown routing mode: {mode}"
        )


def build_star_lookup(
    stars
):

    lookup = {}

    for star in stars:

        lookup[
            star.display_name.lower()
        ] = star

        lookup[
            star.designation.lower()
        ] = star

        lookup[
            str(star.source_id)
        ] = star

    return lookup


def find_star(
    lookup,
    name
):

    return lookup.get(
        name.strip().lower()
    )


def print_route(
    graph,
    route
):

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

    total_distance = 0.0

    for i in range(
        len(route) - 1
    ):

        current_id = route[i]
        next_id = route[i + 1]

        current_star = graph.nodes[
            current_id
        ]["star"]

        distance = graph[
            current_id
        ][
            next_id
        ]["distance"]

        print(
            f"{current_star.display_name}"
        )

        print(
            f"   ↓ {distance:.2f} ly"
        )

        total_distance += distance

    destination_star = graph.nodes[
        route[-1]
    ]["star"]

    print(
        destination_star.display_name
    )

    print()

    print(
        f"Jumps Required: "
        f"{len(route) - 1}"
    )

    print(
        f"Total Distance: "
        f"{total_distance:.2f} ly"
    )