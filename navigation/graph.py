import math

import networkx as nx

from scipy.spatial import cKDTree


def star_distance(
    star_a,
    star_b
):
    """
    Calculate the actual straight-line distance between
    two stars in 3D space.
    """

    ax, ay, az = star_a.xyz()
    bx, by, bz = star_b.xyz()

    dx = bx - ax
    dy = by - ay
    dz = bz - az

    return math.sqrt(
        dx * dx +
        dy * dy +
        dz * dz
    )


def build_navigation_graph(
    stars,
    max_jump_distance
):

    graph = nx.Graph()

    # --------------------------------------------------
    # Add every star as a graph node
    # --------------------------------------------------

    for star in stars:

        graph.add_node(
            star.source_id,
            star=star
        )

    # --------------------------------------------------
    # Create array of XYZ coordinates
    # --------------------------------------------------

    positions = [
        star.xyz()
        for star in stars
    ]

    # --------------------------------------------------
    # Build spatial index
    # --------------------------------------------------

    tree = cKDTree(
        positions
    )

    # --------------------------------------------------
    # Find ALL star pairs within jump range
    # --------------------------------------------------

    pairs = tree.query_pairs(
        r=max_jump_distance
    )

    print(
        f"Found {len(pairs):,} possible jumps."
    )

    # --------------------------------------------------
    # Convert nearby pairs into graph edges
    # --------------------------------------------------

    for i, j in pairs:

        star_a = stars[i]
        star_b = stars[j]

        distance = star_distance(
            star_a,
            star_b
        )

        graph.add_edge(
            star_a.source_id,
            star_b.source_id,

            distance=distance
        )

    return graph


def print_graph_info(
    graph
):

    print()
    print(
        "===== GRAPH INFORMATION ====="
    )

    print(
        f"Stars: "
        f"{graph.number_of_nodes():,}"
    )

    print(
        f"Valid jumps: "
        f"{graph.number_of_edges():,}"
    )

    components = list(
        nx.connected_components(
            graph
        )
    )

    components.sort(
        key=len,
        reverse=True
    )

    print(
        f"Disconnected regions: "
        f"{len(components):,}"
    )

    print(
        f"Largest connected region: "
        f"{len(components[0])} stars"
    )

    percentage = (
        len(components[0])
        /
        graph.number_of_nodes()
        *
        100
    )

    print(
        f"Largest region coverage: "
        f"{percentage:.2f}%"
    )

    print()