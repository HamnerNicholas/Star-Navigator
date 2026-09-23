import math

import networkx as nx

from scipy.spatial import cKDTree

import pickle

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

def save_navigation_graph(
    graph,
    filename,
    max_jump_distance
):

    filename.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Create a cache graph containing only topology + distance
    # --------------------------------------------------------

    cached_graph = nx.Graph()

    cached_graph.add_nodes_from(
        graph.nodes
    )

    for source, target, data in (
        graph.edges(data=True)
    ):

        cached_graph.add_edge(
            source,
            target,
            distance=data["distance"]
        )

    # Store metadata on the cached graph.

    cached_graph.graph[
        "cache_version"
    ] = 1

    cached_graph.graph[
        "max_jump_distance"
    ] = max_jump_distance

    cached_graph.graph[
        "node_count"
    ] = cached_graph.number_of_nodes()

    cached_graph.graph[
        "edge_count"
    ] = cached_graph.number_of_edges()

    # --------------------------------------------------------
    # Write cache
    # --------------------------------------------------------

    with open(
        filename,
        "wb"
    ) as file:

        pickle.dump(
            cached_graph,
            file,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    print()
    print(
        f"Navigation graph cache saved:"
    )

    print(
        f"  {filename}"
    )

def graph_cache_is_valid(
    filename,
    stars,
    max_jump_distance
):

    if not filename.exists():

        return False

    try:

        with open(
            filename,
            "rb"
        ) as file:

            cached_graph = pickle.load(
                file
            )

    except Exception:

        return False

    # --------------------------------------------------------
    # Version
    # --------------------------------------------------------

    if cached_graph.graph.get(
        "cache_version"
    ) != 1:

        return False

    # --------------------------------------------------------
    # Jump distance
    # --------------------------------------------------------

    cached_jump_distance = (
        cached_graph.graph.get(
            "max_jump_distance"
        )
    )

    if (
        cached_jump_distance
        !=
        max_jump_distance
    ):

        return False

    # --------------------------------------------------------
    # Node count
    # --------------------------------------------------------

    if (
        cached_graph.number_of_nodes()
        !=
        len(stars)
    ):

        return False

    # --------------------------------------------------------
    # Node IDs
    # --------------------------------------------------------

    cached_ids = set(
        cached_graph.nodes
    )

    current_ids = {
        star.source_id
        for star in stars
    }

    if cached_ids != current_ids:

        return False

    return True

def load_navigation_graph(
    filename,
    stars
):

    with open(
        filename,
        "rb"
    ) as file:

        graph = pickle.load(
            file
        )

    # --------------------------------------------------------
    # Attach current Star objects
    # --------------------------------------------------------

    stars_by_id = {
        star.source_id: star
        for star in stars
    }

    for source_id in graph.nodes:

        graph.nodes[
            source_id
        ]["star"] = stars_by_id[
            source_id
        ]

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