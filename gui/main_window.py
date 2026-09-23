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
    QListWidget,
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

        self.current_selected_source_id = None

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

        self.web_view.loadFinished.connect(
            self._on_map_loaded
        )

    def _on_map_loaded(
        self,
        success
    ):

        if not success:
            return

        if (
            self.current_selected_source_id
            is None
        ):
            return

        self._update_selected_system(
            self.current_selected_source_id
        )

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

        # ========================================================
        # NAVIGATION GROUP
        # ========================================================

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

        # --------------------------------------------------------
        # Start
        # --------------------------------------------------------

        self.start_input = QLineEdit(
            "Sol"
        )

        self.start_input.setPlaceholderText(
            "Starting system"
        )

        # --------------------------------------------------------
        # Destination
        # --------------------------------------------------------

        self.destination_input = (
            QLineEdit()
        )

        self.destination_input.setPlaceholderText(
            "Destination system"
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

        self.star_name_model = (
            QStringListModel(
                star_names
            )
        )

        self.start_completer = (
            QCompleter(
                self.star_name_model,
                self
            )
        )

        self.destination_completer = (
            QCompleter(
                self.star_name_model,
                self
            )
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
                QCompleter
                .CompletionMode
                .PopupCompletion
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

        # --------------------------------------------------------
        # Route mode
        # --------------------------------------------------------

        self.route_mode = QComboBox()

        self.route_mode.addItem(
            "Shortest Distance",
            "shortest_distance"
        )

        self.route_mode.addItem(
            "Fewest Jumps",
            "fewest_jumps"
        )

        # --------------------------------------------------------
        # Starfield radius
        # --------------------------------------------------------

        self.background_radius = (
            QDoubleSpinBox()
        )

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

        # --------------------------------------------------------
        # Constellation controls
        # --------------------------------------------------------

        self.constellation_check = (
            QCheckBox(
                "Constellation Lines"
            )
        )

        self.constellation_names_check = (
            QCheckBox(
                "Constellation Names"
            )
        )

        self.constellation_check.setChecked(
            False
        )

        self.constellation_names_check.setChecked(
            False
        )

        # --------------------------------------------------------
        # Generate route button
        # --------------------------------------------------------

        self.generate_button = QPushButton(
            "GENERATE ROUTE"
        )

        self.generate_button.clicked.connect(
            self.generate_route
        )

        # --------------------------------------------------------
        # Add navigation controls
        # --------------------------------------------------------

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
            self.constellation_check
        )

        navigation_layout.addRow(
            self.constellation_names_check
        )

        navigation_layout.addRow(
            self.generate_button
        )

        sidebar_layout.addWidget(
            navigation_group
        )

        # ========================================================
        # STATUS
        # ========================================================

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

        # ========================================================
        # ROUTE SUMMARY
        # ========================================================

        route_group = QGroupBox(
            "ROUTE SUMMARY"
        )

        route_layout = QVBoxLayout(
            route_group
        )

        self.route_list = QListWidget()

        self.route_list.currentRowChanged.connect(
            self.route_selection_changed
        )

        route_layout.addWidget(
            self.route_list
        )

        sidebar_layout.addWidget(
            route_group,
            1
        )

        # ========================================================
        # SYSTEM INFORMATION
        # ========================================================

        system_info_group = QGroupBox(
            "SYSTEM INFORMATION"
        )

        system_info_layout = QVBoxLayout(
            system_info_group
        )

        self.system_info = QTextEdit()

        self.system_info.setObjectName(
            "systemInfo"
        )

        self.system_info.setReadOnly(
            True
        )

        self.system_info.setPlaceholderText(
            "Select a system to view details."
        )

        self.system_info.setMinimumHeight(
            250
        )

        system_info_layout.addWidget(
            self.system_info
        )

        sidebar_layout.addWidget(
            system_info_group
        )

        # ========================================================
        # ADD SIDEBAR
        # ========================================================

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

        # --------------------------------------------------------
        # Splitter behavior
        # --------------------------------------------------------

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

            QTextEdit#systemInfo {
                background-color: #080d14;
                border: 1px solid #202b3a;
                border-radius: 5px;
                padding: 10px;
                color: #dbe8f5;
                selection-background-color: #087f98;
                selection-color: white;
            }
            """
    )

    def generate_route(self):

        start_name = (
            self.start_input.text().strip()
        )

        destination_name = (
            self.destination_input.text().strip()
        )

        if (
            not start_name
            or not destination_name
        ):

            self._show_error(
                "Missing destination",
                "Enter both a starting system and a destination."
            )

            return

        # ========================================================
        # FIND STARTING SYSTEM
        # ========================================================

        start_id = find_star(
            self.lookup,
            start_name
        )

        if start_id is None:

            self._show_error(
                "Starting system not found",
                f"Could not find: {start_name}"
            )

            return

        # ========================================================
        # FIND DESTINATION
        # ========================================================

        destination_id = find_star(
            self.lookup,
            destination_name
        )

        if destination_id is None:

            self._show_error(
                "Destination not found",
                f"Could not find: {destination_name}"
            )

            return

        # ========================================================
        # GET DISPLAY NAMES
        # ========================================================

        start_star = self.graph.nodes[
            start_id
        ]["star"]

        destination_star = (
            self.graph.nodes[
                destination_id
            ]["star"]
        )

        # ========================================================
        # ROUTE MODE
        # ========================================================

        mode = (
            self.route_mode.currentData()
        )

        # ========================================================
        # CALCULATE ROUTE
        # ========================================================

        try:

            route = find_route(
                self.graph,
                start_id,
                destination_id,
                mode=mode,
            )

        except nx.NetworkXNoPath:

            self._show_error(
                "No route",
                (
                    f"No route exists from "
                    f"{start_star.display_name} "
                    f"to "
                    f"{destination_star.display_name} "
                    f"with a "
                    f"{MAX_JUMP_DISTANCE:.1f} ly "
                    f"jump range."
                ),
            )

            return

        # ========================================================
        # STORE ROUTE
        # ========================================================

        self.current_route = route

        self.status_label.setText(
            f"Route found: "
            f"{len(route) - 1} jumps"
        )

        # ========================================================
        # UPDATE ROUTE SUMMARY
        # ========================================================

        self._update_route_text(
            route
        )

        # ========================================================
        # UPDATE SYSTEM INFORMATION
        # ========================================================

        if self.route_list.count() > 0:

            self.route_list.setCurrentRow(
                0
            )

        # ========================================================
        # UPDATE MAP
        # ========================================================

        self._update_map(
            route
        )

    def _update_route_text(self, route):

        self.current_route = route

        self.route_list.clear()

        for source_id in route:

            star = self.graph.nodes[
                source_id
            ]["star"]

            self.route_list.addItem(
                star.display_name
            )

        if self.route_list.count() > 0:

            self.route_list.setCurrentRow(
                0
            )

    def _update_map(
        self,
        route
    ):

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

            draw_interactive_map(
                graph=self.graph,
                stars=self.stars,
                route=route,
                filename=INTERACTIVE_MAP_FILE,
                background_radius=background_radius,
                show_constellations=(
                    show_constellations
                ),
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

    def route_selection_changed(
        self,
        row
    ):

        if self.current_route is None:

            self.clear_system_info()

            return

        if row < 0:

            self.clear_system_info()

            return

        if row >= len(
            self.current_route
        ):

            self.clear_system_info()

            return

        source_id = (
            self.current_route[row]
        )

        star = self.graph.nodes[
            source_id
        ]["star"]

        self.show_system_info(
            star,
            row
        )

        self.current_selected_source_id = (
            source_id
        )

        self._update_selected_system(
            source_id
        )

    def show_system_info(
        self,
        star,
        route_index=None
    ):

        text = []

        # ========================================================
        # SYSTEM
        # ========================================================

        text.append(
            f"<h2>{star.display_name}</h2>"
        )

        text.append(
            "<b>Catalog</b>"
        )

        text.append(
            f"Gaia DR3: {star.source_id}"
        )

        text.append(
            "<br>"
        )

        # ========================================================
        # POSITION
        # ========================================================

        text.append(
            "<b>Position</b>"
        )

        text.append(
            f"Distance from Sol: "
            f"{star.distance_ly:.2f} ly"
        )

        text.append(
            f"Right Ascension: "
            f"{star.ra_deg:.4f}°"
        )

        text.append(
            f"Declination: "
            f"{star.dec_deg:.4f}°"
        )

        # ========================================================
        # PHOTOMETRY
        # ========================================================

        text.append(
            "<br><b>Photometry</b>"
        )

        if star.magnitude is not None:

            text.append(
                f"G Magnitude: "
                f"{star.magnitude:.2f}"
            )

        else:

            text.append(
                "G Magnitude: Unavailable"
            )

        if star.bp_rp is not None:

            text.append(
                f"BP-RP: "
                f"{star.bp_rp:.2f}"
            )

        else:

            text.append(
                "BP-RP: Unavailable"
            )

        # ========================================================
        # MOTION
        # ========================================================

        text.append(
            "<br><b>Motion</b>"
        )

        if star.pmra is not None:

            text.append(
                f"Proper Motion RA: "
                f"{star.pmra:.2f} mas/yr"
            )

        else:

            text.append(
                "Proper Motion RA: Unavailable"
            )

        if star.pmdec is not None:

            text.append(
                f"Proper Motion Dec: "
                f"{star.pmdec:.2f} mas/yr"
            )

        else:

            text.append(
                "Proper Motion Dec: Unavailable"
            )

        if star.radial_velocity is not None:

            text.append(
                f"Radial Velocity: "
                f"{star.radial_velocity:.2f} km/s"
            )

        else:

            text.append(
                "Radial Velocity: Unavailable"
            )

        # ========================================================
        # ROUTE INFORMATION
        # ========================================================

        if (
            route_index is not None
            and
            self.current_route is not None
        ):

            text.append(
                "<br><b>Route Information</b>"
            )

            text.append(
                f"Route Stop: "
                f"{route_index + 1} "
                f"of "
                f"{len(self.current_route)}"
            )

            # --------------------------------------------
            # Previous jump
            # --------------------------------------------

            if route_index > 0:

                previous_id = (
                    self.current_route[
                        route_index - 1
                    ]
                )

                previous_star = (
                    self.graph.nodes[
                        previous_id
                    ]["star"]
                )

                jump_distance = (
                    self.graph[
                        previous_id
                    ][
                        star.source_id
                    ]["distance"]
                )

                text.append(
                    f"Previous: "
                    f"{previous_star.display_name}"
                )

                text.append(
                    f"Previous Jump: "
                    f"{jump_distance:.2f} ly"
                )

            # --------------------------------------------
            # Next jump
            # --------------------------------------------

            if (
                route_index
                <
                len(self.current_route) - 1
            ):

                next_id = (
                    self.current_route[
                        route_index + 1
                    ]
                )

                next_star = (
                    self.graph.nodes[
                        next_id
                    ]["star"]
                )

                jump_distance = (
                    self.graph[
                        star.source_id
                    ][
                        next_id
                    ]["distance"]
                )

                text.append(
                    f"Next: "
                    f"{next_star.display_name}"
                )

                text.append(
                    f"Next Jump: "
                    f"{jump_distance:.2f} ly"
                )

        self.system_info.setHtml(
            "<br>".join(text)
        )

    def clear_system_info(
        self
    ):

        self.system_info.clear()

        self.system_info.setPlaceholderText(
            "Select a system to view details."
        )

    def _update_selected_system(
        self,
        source_id
    ):

        if source_id not in self.graph.nodes:
            return

        star = self.graph.nodes[
            source_id
        ]["star"]

        x, y, z = star.xyz()

        javascript = f"""
        (() => {{

            const graph = document.getElementById(
                "starNavigatorPlot"
            );

            if (!graph || !graph.data) {{
                return false;
            }}

            const traceIndex = graph.data.findIndex(
                trace =>
                    trace.name === "Selected System"
            );

            if (traceIndex === -1) {{
                console.log(
                    "Selected System trace not found"
                );

                return false;
            }}

            Plotly.restyle(
                graph,
                {{
                    x: [[{x}]],
                    y: [[{y}]],
                    z: [[{z}]],
                    visible: true
                }},
                [traceIndex]
            );

            return true;

        }})();
        """

        self.web_view.page().runJavaScript(
            javascript,
            lambda result: print(
                "Highlight updated:",
                result
            )
        )