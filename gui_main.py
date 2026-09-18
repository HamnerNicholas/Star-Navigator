import sys

from PySide6.QtWidgets import QApplication

from Star_Navigator.catalog import (
    add_sol,
    load_gaia_catalog,
    load_star_names,
)
from Star_Navigator.config import (
    CATALOG_FILE,
    MAX_JUMP_DISTANCE,
    STAR_NAME_FILE,
)
from Star_Navigator.gui.main_window import MainWindow
from Star_Navigator.navigation.graph import build_navigation_graph
from Star_Navigator.navigation.routing import build_star_lookup


def main():
    star_names = load_star_names(STAR_NAME_FILE)
    stars = load_gaia_catalog(
        CATALOG_FILE,
        star_names,
    )
    add_sol(stars)

    graph = build_navigation_graph(
        stars,
        MAX_JUMP_DISTANCE,
    )

    lookup = build_star_lookup(stars)

    app = QApplication(sys.argv)
    window = MainWindow(
        graph,
        stars,
        lookup,
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
