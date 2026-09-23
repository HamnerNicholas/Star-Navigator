import sys

from PySide6.QtWidgets import QApplication

from Star_Navigator.config import (
    CATALOG_FILE,
    STAR_NAME_FILE,
    GRAPH_CACHE_FILE,
    MAX_JUMP_DISTANCE,
)

from Star_Navigator.catalog import (
    load_star_names,
    load_gaia_catalog,
)

from Star_Navigator.navigation.graph import (
    build_navigation_graph,
    load_navigation_graph,
    save_navigation_graph,
    graph_cache_is_valid,
)
from Star_Navigator.gui.main_window import MainWindow
from Star_Navigator.navigation.graph import build_navigation_graph
from Star_Navigator.navigation.routing import build_star_lookup


def main():

    print(
        "Loading star names..."
    )

    star_names = load_star_names(
        STAR_NAME_FILE
    )

    stars = load_gaia_catalog(
        CATALOG_FILE,
        star_names
    )

    # --------------------------------------------------------
    # Load cached graph or build it
    # --------------------------------------------------------

    if graph_cache_is_valid(
        GRAPH_CACHE_FILE,
        stars,
        MAX_JUMP_DISTANCE
    ):

        print(
            "Loading cached navigation graph..."
        )

        graph = load_navigation_graph(
            GRAPH_CACHE_FILE,
            stars
        )

    else:

        print(
            "Building navigation graph..."
        )

        graph = build_navigation_graph(
            stars,
            MAX_JUMP_DISTANCE
        )

        save_navigation_graph(
            graph,
            GRAPH_CACHE_FILE,
            MAX_JUMP_DISTANCE
        )

    # --------------------------------------------------------
    # Launch GUI
    # --------------------------------------------------------

    app = QApplication(
        sys.argv
    )

    window = MainWindow(
        graph,
        stars
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
