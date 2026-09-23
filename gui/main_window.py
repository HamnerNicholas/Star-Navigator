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
from PySide6.QtWidgets import QCheckBox

import networkx as nx

from ..config import BACKGROUND_RADIUS, INTERACTIVE_MAP_FILE, MAX_JUMP_DISTANCE
from ..navigation.routing import find_route, find_star, print_route
from ..renderers.interactive import draw_interactive_map


class MainWindow(QMainWindow):
    def __init__(self, graph, stars):
        super().__init__()

        self.graph = graph
        self.stars = stars

        self.lookup = {
            star.display_name.lower():
            star.source_id
            for star in stars
        }

        self.current_route = None
        self.current_figure = None

        self.setWindowTitle("Star Navigator")
        self.resize(1500, 950)

        self._build_ui()
        self._apply_style()

    def _build_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        root_layout = QVBoxLayout(
            central
        )

        root_layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        root_layout.setSpacing(
            10
        )

        # ========================================================
        # HEADER
        # ========================================================

        header = QLabel(
            "STAR NAVIGATOR"
        )

        header.setObjectName(
            "appTitle"
        )

        root_layout.addWidget(
            header
        )

        # ========================================================
        # MAIN SPLITTER
        # ========================================================

        main_splitter = QSplitter()

        # ========================================================
        # LEFT SIDEBAR
        # ========================================================

        sidebar = QWidget()

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        sidebar_layout.setSpacing(
            12
        )

        # --------------------------------------------------------
        # Navigation group
        # --------------------------------------------------------

        navigation_group = QGroupBox(
            "NAVIGATION"
        )

        navigation_layout = QFormLayout(
            navigation_group
        )

        navigation_layout.setContentsMargins(
            12,
            14,
            12,
            12
        )

        navigation_layout.setSpacing(
            10
        )

        self.start_input = QLineEdit(
            "Sol"
        )

        self.start_input.setPlaceholderText(
            "Starting system"
        )

        self.destination_input = QLineEdit()

        self.destination_input.setPlaceholderText(
            "Destination system"
        )

        self.constellation_check = QCheckBox(
            "Constellation Lines"
        )

        self.constellation_names_check = QCheckBox(
            "Constellation Names"
        )

        self.constellation_check.setChecked(
            False
        )

        self.constellation_names_check.setChecked(
            False
        )

        navigation_layout.addRow(
            self.constellation_check
        )

        navigation_layout.addRow(
            self.constellation_names_check
        )

        navigation_layout.addRow(
            self.constellation_check
        )

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

            completer.setMaxVisibleItems(
                12
            )

        self.start_input.setCompleter(
            self.start_completer
        )

        self.destination_input.setCompleter(
            self.destination_completer
        )

        self.route_mode = QComboBox()

        self.route_mode.addItem(
            "Shortest Distance",
            "shortest_distance"
        )

        self.route_mode.addItem(
            "Fewest Jumps",
            "fewest_jumps"
        )

        self.background_radius = QDoubleSpinBox()

        self.background_radius.setRange(
            1.0,
            200.0
        )

        self.background_radius.setSingleStep(
            5.0
        )

        self.background_radius.setDecimals(
            1
        )

        self.background_radius.setValue(
            BACKGROUND_RADIUS
        )

        self.background_radius.setSuffix(
            " ly"
        )

        self.generate_button = QPushButton(
            "GENERATE ROUTE"
        )

        self.generate_button.clicked.connect(
            self.generate_route
        )

        navigation_layout.addRow(
            "Start",
            self.start_input
        )

        navigation_layout.addRow(
            "Destination",
            self.destination_input
        )

        navigation_layout.addRow(
            "Route",
            self.route_mode
        )

        navigation_layout.addRow(
            "Starfield",
            self.background_radius
        )

        navigation_layout.addRow(
            self.generate_button
        )

        sidebar_layout.addWidget(
            navigation_group
        )

        # --------------------------------------------------------
        # Status
        # --------------------------------------------------------

        status_group = QGroupBox(
            "STATUS"
        )

        status_layout = QVBoxLayout(
            status_group
        )

        self.status_label = QLabel(
            "Ready"
        )

        self.status_label.setObjectName(
            "statusLabel"
        )

        self.status_label.setWordWrap(
            True
        )

        status_layout.addWidget(
            self.status_label
        )

        sidebar_layout.addWidget(
            status_group
        )

        # --------------------------------------------------------
        # Route information
        # --------------------------------------------------------

        route_group = QGroupBox(
            "ROUTE SUMMARY"
        )

        route_layout = QVBoxLayout(
            route_group
        )

        self.route_text = QTextEdit()

        self.route_text.setReadOnly(
            True
        )

        route_layout.addWidget(
            self.route_text
        )

        sidebar_layout.addWidget(
            route_group,
            1
        )

        # --------------------------------------------------------
        # Add sidebar
        # --------------------------------------------------------

        main_splitter.addWidget(
            sidebar
        )

        # ========================================================
        # MAP
        # ========================================================

        self.web_view = QWebEngineView()

        main_splitter.addWidget(
            self.web_view
        )

        main_splitter.setStretchFactor(
            0,
            0
        )

        main_splitter.setStretchFactor(
            1,
            1
        )

        main_splitter.setSizes([
            350,
            1150
        ])

        root_layout.addWidget(
            main_splitter,
            1
        )

    def _apply_style(self):

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #090d14;
            }

            QWidget {
                color: #d9e2f0;
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QLabel#appTitle {
                color: #ffffff;
                font-size: 18pt;
                font-weight: 600;
                padding: 6px 8px;
            }

            QGroupBox {
                background-color: #0d131d;
                border: 1px solid #202b3a;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #7fdfff;
                font-weight: 600;
            }

             QLineEdit,
            QComboBox,
            QDoubleSpinBox {
                background-color: #111a26;
                border: 1px solid #2a394d;
                border-radius: 5px;
                padding: 7px 8px;
                color: #edf5ff;
                selection-background-color: #008fa8;
                selection-color: white;
            }

            QLineEdit:hover,
            QComboBox:hover,
            QDoubleSpinBox:hover {
                border: 1px solid #3b5068;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDoubleSpinBox:focus {
                background-color: #121e2c;
                border: 1px solid #00d9ff;
            }

            QComboBox QAbstractItemView {
                background-color: #111a26;
                border: 1px solid #2a394d;
                color: #ffffff;
                selection-background-color: #087f98;
                selection-color: #ffffff;
                outline: none;
            }

            QPushButton {
                background-color: #008fa8;
                border: none;
                border-radius: 6px;
                padding: 9px 12px;
                color: white;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #00a9c7;
            }

            QPushButton:pressed {
                background-color: #00798f;
            }

            QTextEdit {
                background-color: #080d14;
                border: 1px solid #202b3a;
                border-radius: 5px;
                color: #dbe8f5;
                font-family: Consolas;
                font-size: 9pt;
            }

            QLabel#statusLabel {
                color: #7fdfff;
                padding: 4px;
            }

            QSplitter::handle {
                background-color: #182230;
                width: 2px;
            }

            QScrollBar:vertical {
                background: #0a1018;
                width: 10px;
            }

            QScrollBar::handle:vertical {
                background: #2a394d;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #3b5068;
            }

            QListWidget {
                background-color: #080d14;
                border: 1px solid #202b3a;
                border-radius: 5px;
                color: #dbe8f5;
                outline: none;
            }

            QListWidget::item {
                padding: 7px 6px;
                border-radius: 4px;
            }

            QListWidget::item:hover {
                background-color: #142333;
            }

            QListWidget::item:selected {
                background-color: #087f98;
                color: white;
                border: 1px solid #00d9ff;
            }

            QListWidget::item:selected:active {
                background-color: #087f98;
                color: white;
            }

            QLabel#systemInfo {
                background-color: #080d14;
                border: 1px solid #202b3a;
                border-radius: 5px;
                padding: 10px;
                color: #dbe8f5;
            }
            """
    )

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
        background_radius = (
            self.background_radius.value()
        )

        show_constellations = (
            self.constellation_check.isChecked()
        )

        show_constellation_names = (
            self.constellation_names_check.isChecked()
        )

        try:
            output_file = Path(INTERACTIVE_MAP_FILE)

            print(
                "Constellations:",
                self.constellation_check.isChecked()
            )

            draw_interactive_map(
                graph=self.graph,
                stars=self.stars,
                route=route,
                filename=INTERACTIVE_MAP_FILE,
                background_radius=background_radius,
                show_constellations=show_constellations,
                show_constellation_names=(
                    show_constellation_names
                    and show_constellations
                )
            )

            self.web_view.setUrl(
                QUrl.fromLocalFile(
                    str(INTERACTIVE_MAP_FILE)
                )
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

    