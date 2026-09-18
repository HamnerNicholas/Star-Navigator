from pathlib import Path

from PySide6.QtCore import (
    QUrl,
    Qt,
    QStringListModel,
)

from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

import networkx as nx

from ..config import BACKGROUND_RADIUS, INTERACTIVE_MAP_FILE, MAX_JUMP_DISTANCE
from ..navigation.routing import find_route, find_star, print_route
from ..renderers.interactive import draw_interactive_map


class MainWindow(QMainWindow):
    def __init__(self, graph, stars, lookup):
        super().__init__()

        self.graph = graph
        self.stars = stars
        self.lookup = lookup

        self.current_route = None
        self.current_figure = None

        self.setWindowTitle("Star Navigator")
        self.resize(1500, 950)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        controls = QGroupBox("Navigation")
        controls_layout = QFormLayout(controls)

        self.start_input = QLineEdit("Sol")
        self.start_input.setPlaceholderText("Starting system")

        self.destination_input = QLineEdit()
        self.destination_input.setPlaceholderText("Destination system")

        # ========================================================
        # STAR NAME AUTOCOMPLETE
        # ========================================================

        star_names = sorted(
            {
                star.display_name
                for star in self.stars
                if star.display_name
            },
            key=str.lower
        )

        self.star_name_model = QStringListModel(
            star_names
        )

        self.start_completer = QCompleter(
            self.star_name_model,
            self
        )

        self.destination_completer = QCompleter(
            self.star_name_model,
            self
        )

        for completer in (
            self.start_completer,
            self.destination_completer
        ):

            completer.setCaseSensitivity(
                Qt.CaseSensitivity.CaseInsensitive
            )

            completer.setFilterMode(
                Qt.MatchFlag.MatchContains
            )

            completer.setCompletionMode(
                QCompleter.CompletionMode.PopupCompletion
            )

        self.start_input.setCompleter(
            self.start_completer
        )

        self.destination_input.setCompleter(
            self.destination_completer
        )

        self.route_mode = QComboBox()
        self.route_mode.addItem("Shortest Distance", "shortest_distance")
        self.route_mode.addItem("Fewest Jumps", "fewest_jumps")

        self.background_radius = QDoubleSpinBox()
        self.background_radius.setRange(1.0, 100.0)
        self.background_radius.setSingleStep(5.0)
        self.background_radius.setDecimals(1)
        self.background_radius.setValue(BACKGROUND_RADIUS)
        self.background_radius.setSuffix(" ly")

        self.generate_button = QPushButton("Generate Route")
        self.generate_button.clicked.connect(self.generate_route)

        self.status_label = QLabel("Ready")

        controls_layout.addRow("Start:", self.start_input)
        controls_layout.addRow("Destination:", self.destination_input)
        controls_layout.addRow("Route:", self.route_mode)
        controls_layout.addRow("Background:", self.background_radius)
        controls_layout.addRow(self.generate_button)
        controls_layout.addRow("Status:", self.status_label)

        root_layout.addWidget(controls)

        splitter = QSplitter()

        route_panel = QWidget()
        route_layout = QVBoxLayout(route_panel)
        route_layout.setContentsMargins(8, 8, 8, 8)

        route_title = QLabel("Route Information")
        route_layout.addWidget(route_title)

        self.route_text = QTextEdit()
        self.route_text.setReadOnly(True)
        route_layout.addWidget(self.route_text)

        splitter.addWidget(route_panel)

        self.web_view = QWebEngineView()
        splitter.addWidget(self.web_view)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 1100])

        root_layout.addWidget(splitter, 1)

    def generate_route(self):
        start_name = self.start_input.text().strip()
        destination_name = self.destination_input.text().strip()

        if not start_name or not destination_name:
            self._show_error(
                "Missing destination",
                "Enter both a starting system and a destination."
            )
            return

        start = find_star(self.lookup, start_name)
        if start is None:
            self._show_error(
                "Starting system not found",
                f"Could not find: {start_name}"
            )
            return

        destination = find_star(self.lookup, destination_name)
        if destination is None:
            self._show_error(
                "Destination not found",
                f"Could not find: {destination_name}"
            )
            return

        mode = self.route_mode.currentData()

        try:
            route = find_route(
                self.graph,
                start.source_id,
                destination.source_id,
                mode=mode,
            )
        except nx.NetworkXNoPath:
            self._show_error(
                "No route",
                (
                    f"No route exists from {start.display_name} "
                    f"to {destination.display_name} "
                    f"with a {MAX_JUMP_DISTANCE:.1f} ly jump range."
                ),
            )
            return

        self.current_route = route
        self.status_label.setText(
            f"Route found: {len(route) - 1} jumps"
        )

        self._update_route_text(route)
        self._update_map(route)

    def _update_route_text(self, route):
        lines = []
        total_distance = 0.0

        for i in range(len(route) - 1):
            current_id = route[i]
            next_id = route[i + 1]

            current_star = self.graph.nodes[current_id]["star"]
            next_star = self.graph.nodes[next_id]["star"]
            distance = self.graph[current_id][next_id]["distance"]

            total_distance += distance

            if i == 0:
                lines.append(f"START: {current_star.display_name}")
            else:
                lines.append(current_star.display_name)

            lines.append(f"   ↓ {distance:.2f} ly")

        destination = self.graph.nodes[route[-1]]["star"]
        lines.append(f"DESTINATION: {destination.display_name}")
        lines.append("")
        lines.append(f"Jumps: {len(route) - 1}")
        lines.append(f"Total distance: {total_distance:.2f} ly")
        lines.append(f"Maximum jump: {MAX_JUMP_DISTANCE:.2f} ly")

        self.route_text.setPlainText("\n".join(lines))

    def _update_map(self, route):
        try:
            output_file = Path(INTERACTIVE_MAP_FILE)

            figure = draw_interactive_map(
                self.graph,
                self.stars,
                route,
                filename=output_file,
                background_radius=self.background_radius.value(),
            )

            self.web_view.setUrl(
                QUrl.fromLocalFile(
                    str(INTERACTIVE_MAP_FILE)
                )
            )

            self.current_figure = figure

            html = figure.to_html(
                include_plotlyjs=True,
                full_html=True,
            )

            self.web_view.setHtml(
                html,
                QUrl.fromLocalFile(str(output_file.parent.resolve()) + "/"),
            )

        except Exception as error:
            self._show_error(
                "Map rendering failed",
                str(error),
            )

    def _show_error(self, title, message):
        self.status_label.setText("Error")
        QMessageBox.critical(
            self,
            title,
            message,
        )

    