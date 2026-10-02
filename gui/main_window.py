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
    QInputDialog,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QHeaderView,
    QAbstractItemView,
    QFileDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QCheckBox

import networkx as nx

from ..config import BACKGROUND_RADIUS, INTERACTIVE_MAP_FILE, MAX_JUMP_DISTANCE
from ..navigation.routing import find_route, find_star, print_route
from ..renderers.interactive import draw_interactive_map

from ..dm import (
    Trait,
    save_profile,
    load_profile,
)

from ..dm.generator import (
    generate_route_traits,
)

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

        self.dm_traits = []

        self.current_dm_profile = None

        self.setWindowTitle("Star Navigator")
        self.resize(1500, 950)

        self._build_ui()
        self._apply_style()

        self.web_view.loadFinished.connect(
            self._on_map_loaded
        )
    def _build_dm_tab(self):

        dm_tab = QWidget()

        dm_layout = QVBoxLayout(
            dm_tab
        )

        dm_layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        dm_layout.setSpacing(
            12
        )

        # ========================================================
        # TRAIT DEFINITIONS
        # ========================================================

        trait_group = QGroupBox(
            "TRAIT DEFINITIONS"
        )

        trait_layout = QVBoxLayout(
            trait_group
        )

        self.trait_table = QTableWidget()

        self.trait_table.setColumnCount(
            4
        )

        self.trait_table.setHorizontalHeaderLabels([
            "Trait",
            "Type",
            "Probability",
            "Range"
        ])

        self.trait_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.trait_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.trait_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.trait_table.verticalHeader().setVisible(
            False
        )
        self.trait_table.verticalHeader().setDefaultSectionSize(
            34
        )

        header = (
            self.trait_table
            .horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents
        )

        trait_layout.addWidget(
            self.trait_table
        )

        # --------------------------------------------------------
        # Trait buttons
        # --------------------------------------------------------

        trait_buttons = QHBoxLayout()

        self.add_trait_button = QPushButton(
            "+ ADD TRAIT"
        )

        self.remove_trait_button = QPushButton(
            "REMOVE SELECTED"
        )

        self.save_profile_button = QPushButton(
            "SAVE PROFILE"
        )

        self.load_profile_button = QPushButton(
            "LOAD PROFILE"
        )

        self.edit_trait_button = QPushButton(
            "EDIT NAME"
        )


        self.save_profile_button.clicked.connect(
            self._save_dm_profile
        )

        self.load_profile_button.clicked.connect(
            self._load_dm_profile
        )

        trait_buttons.addWidget(
            self.add_trait_button
        )

        trait_buttons.addWidget(
            self.remove_trait_button
        )

        trait_buttons.addWidget(
            self.save_profile_button
        )

        trait_buttons.addWidget(
            self.load_profile_button
        )

        trait_buttons.addWidget(
            self.edit_trait_button
        )

        trait_buttons.addStretch()

        self.add_trait_button.clicked.connect(
            self._add_trait
        )

        self.remove_trait_button.clicked.connect(
            self._remove_selected_trait
        )

        self.edit_trait_button.clicked.connect(
            self._edit_trait_name
        )

        trait_buttons.addWidget(
            self.add_trait_button
        )

        trait_buttons.addWidget(
            self.remove_trait_button
        )

        trait_buttons.addStretch()

        trait_layout.addLayout(
            trait_buttons
        )

        trait_buttons.setSpacing(
            8
        )

        dm_layout.addWidget(
            trait_group,
            1
        )

        # ========================================================
        # GENERATION
        # ========================================================

        self.generate_dm_button = QPushButton(
            "GENERATE CURRENT ROUTE"
        )

        self.generate_dm_button.clicked.connect(
            self._generate_dm_route
        )

        dm_layout.addWidget(
            self.generate_dm_button
        )

        # ========================================================
        # RESULTS
        # ========================================================

        results_group = QGroupBox(
            "GENERATED ROUTE DATA"
        )

        results_layout = QVBoxLayout(
            results_group
        )

        self.dm_results = QTextEdit()

        self.dm_results.setReadOnly(
            True
        )

        self.dm_results.setPlaceholderText(
            "Generate a route to see procedural results."
        )

        self.dm_results.setObjectName(
            "dmResults"
        )

        results_layout.addWidget(
            self.dm_results
        )

        dm_layout.addWidget(
            results_group,
            1
        )

        self.tabs.addTab(
            dm_tab,
            "DM GENERATOR"
        )

    def _edit_trait_name(self):

        row = self.trait_table.currentRow()

        if row < 0:
            return

        trait = self.dm_traits[row]

        name, accepted = QInputDialog.getText(
            self,
            "Edit Trait Name",
            "Trait name:",
            text=trait.name
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        trait.name = name

        self.trait_table.item(
            row,
            0
        ).setText(
            trait.name
        )

    def _save_dm_profile(
        self
    ):

        if not self.dm_traits:

            self._show_error(
                "No traits",
                "Add at least one trait before saving a profile."
            )

            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save DM Profile",
            "",
            "Star Navigator Profile (*.json)"
        )

        if not filename:
            return

        try:

            save_profile(
                filename,
                self.dm_traits
            )

            self.current_dm_profile = filename

            self.status_label.setText(
                f"DM profile saved: "
                f"{Path(filename).name}"
            )

        except Exception as error:

            self._show_error(
                "Profile save failed",
                str(error)
            )

    def _load_dm_profile(
        self
    ):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load DM Profile",
            "",
            "Star Navigator Profile (*.json)"
        )

        if not filename:
            return

        try:

            traits = load_profile(
                filename
            )

        except Exception as error:

            self._show_error(
                "Profile load failed",
                str(error)
            )

            return

        self.dm_traits = traits

        self.current_dm_profile = filename

        self._refresh_trait_table()

        self.dm_results.clear()

        self.status_label.setText(
            f"DM profile loaded: "
            f"{Path(filename).name}"
        )

    def _refresh_trait_table(
        self
    ):

        self.trait_table.setRowCount(
            0
        )

        for trait in self.dm_traits:

            self._add_trait_to_table(
                trait,
                store=False
            )

    def _add_trait(self):

        # ========================================================
        # TRAIT NAME
        # ========================================================

        name, accepted = QInputDialog.getText(
            self,
            "Add Trait",
            "Trait name:"
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            return

        # ========================================================
        # TRAIT TYPE
        # ========================================================

        trait_type, accepted = QInputDialog.getItem(
            self,
            "Trait Type",
            "Trait type:",
            [
                "Boolean",
                "Range"
            ],
            0,
            False
        )

        if not accepted:
            return

        trait_type = trait_type.lower()

        # ========================================================
        # PROBABILITY
        # ========================================================

        probability, accepted = QInputDialog.getDouble(
            self,
            "Trait Probability",
            "Probability (%):",
            10.0,
            0.0,
            100.0,
            1
        )

        if not accepted:
            return

        # ========================================================
        # RANGE SETTINGS
        # ========================================================

        minimum = None
        maximum = None

        if trait_type == "range":

            minimum, accepted = QInputDialog.getInt(
                self,
                "Trait Minimum",
                "Minimum value:",
                0,
                -2147483648,
                2147483647,
                1
            )

            if not accepted:
                return

            maximum, accepted = QInputDialog.getInt(
                self,
                "Trait Maximum",
                "Maximum value:",
                10,
                -2147483648,
                2147483647,
                1
            )

            if not accepted:
                return

            if minimum > maximum:

                self._show_error(
                    "Invalid range",
                    "Minimum cannot be greater than maximum."
                )

                return

        # ========================================================
        # CREATE TRAIT
        # ========================================================

        try:

            trait = Trait.create(
                name,
                probability / 100.0,
                trait_type,
                minimum,
                maximum
            )

        except ValueError as error:

            self._show_error(
                "Invalid trait",
                str(error)
            )

            return

        self._add_trait_to_table(
            trait
        )

    def _add_trait_to_table(
        self,
        trait,
        store=True
    ):
        if store:

            self.dm_traits.append(
                trait
            )

        row = (
            self.trait_table.rowCount()
        )

        self.trait_table.insertRow(
            row
        )

        # --------------------------------------------------------
        # NAME
        # --------------------------------------------------------

        self.trait_table.setItem(
            row,
            0,
            QTableWidgetItem(
                trait.name
            )
        )

        # --------------------------------------------------------
        # TYPE
        # --------------------------------------------------------

        self.trait_table.setItem(
            row,
            1,
            QTableWidgetItem(
                trait.trait_type.title()
            )
        )

        # --------------------------------------------------------
        # PROBABILITY
        # --------------------------------------------------------

        self.trait_table.setItem(
            row,
            2,
            QTableWidgetItem(
                f"{trait.probability_percent:.1f}%"
            )
        )

        # --------------------------------------------------------
        # RANGE
        # --------------------------------------------------------

        if trait.trait_type == "range":

            range_text = (
                f"{trait.minimum}"
                f" - "
                f"{trait.maximum}"
            )

        else:

            range_text = "—"

        self.trait_table.setItem(
            row,
            3,
            QTableWidgetItem(
                range_text
            )
        )

    def _remove_selected_trait(
        self
    ):

        row = (
            self.trait_table.currentRow()
        )

        if row < 0:
            return

        self.trait_table.removeRow(
            row
        )

        self.dm_traits.pop(
            row
        )

    def _generate_dm_route(
        self
    ):

        if not self.current_route:

            self._show_error(
                "No route",
                "Generate a navigation route first."
            )

            return

        if not self.dm_traits:

            self._show_error(
                "No traits",
                "Add at least one procedural trait."
            )

            return

        # Temporary diagnostic output.
        print()
        print(
            "===== DM TRAITS ====="
        )

        for trait in self.dm_traits:

            print(
                f"{trait.name} | "
                f"{trait.trait_type} | "
                f"{trait.probability_percent:.1f}%"
            )

        results = generate_route_traits(
            self.current_route,
            self.dm_traits
        )

        self._display_dm_results(
            results,
            self.dm_traits
        )

    def _display_dm_results(
        self,
        results,
        traits
    ):

        trait_lookup = {
            trait.id: trait
            for trait in traits
        }

        lines = []

        for source_id in self.current_route:

            star = self.graph.nodes[
                source_id
            ]["star"]

            lines.append(
                f"<h3>{star.display_name}</h3>"
            )

            # ----------------------------------------------------
            # SOL
            # ----------------------------------------------------

            if source_id == 0:

                lines.append(
                    "<i>"
                    "Manual system — procedural "
                    "generation disabled."
                    "</i>"
                )

                lines.append(
                    "<hr>"
                )

                continue

            # ----------------------------------------------------
            # GENERATED TRAITS
            # ----------------------------------------------------

            generated = results.get(
                source_id,
                {}
            )

            if not generated:

                lines.append(
                    "No generated traits."
                )

            else:

                for trait_id, value in (
                    generated.items()
                ):

                    trait = trait_lookup.get(
                        trait_id
                    )

                    if trait is None:
                        continue

                    # Boolean trait

                    if (
                        trait.trait_type
                        ==
                        "boolean"
                    ):

                        lines.append(
                            f"<span style='color:#7fffaf;'>"
                            f"✓ {trait.name}"
                            f"</span>"
                        )

                    # Range trait

                    elif (
                        trait.trait_type
                        ==
                        "range"
                    ):

                        lines.append(
                            f"<span style='color:#7fffaf;'>"
                            f"✓ {trait.name}: {value}"
                            f"</span>"
                        )

            lines.append(
                "<hr>"
            )

        self.dm_results.setHtml(
            "<br>".join(lines)
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
        # TABS
        # ========================================================

        self.tabs = QTabWidget()

        root_layout.addWidget(
            self.tabs,
            1
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

        # Match the empty map area to the application background
        self.web_view.setHtml(
            """
            <!DOCTYPE html>
            <html>
                <head>
                    <style>
                        html, body {
                            margin: 0;
                            padding: 0;
                            width: 100%;
                            height: 100%;
                            background-color: #090d14;
                        }
                    </style>
                </head>

                <body>
                </body>
            </html>
            """
        )

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

        self.tabs.addTab(
            main_splitter,
            "NAVIGATION"
        )

        self._build_dm_tab()

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

            QTableWidget {
                background-color: #080d14;
                alternate-background-color: #0d131d;
                border: 1px solid #202b3a;
                border-radius: 5px;
                color: #dbe8f5;
                gridline-color: #202b3a;
            }

            QTableWidget::item {
                padding: 6px;
            }

            QTableWidget::item:selected {
                background-color: #087f98;
                color: white;
            }

            QHeaderView::section {
                background-color: #111a26;
                border: none;
                border-bottom: 1px solid #2a394d;
                color: #7fdfff;
                font-weight: 600;
                padding: 6px;
            }

            QTabWidget::pane {
                background-color: #090d14;
                border: 1px solid #202b3a;
                border-radius: 6px;
            }

            QTabBar::tab {
                background-color: #0d131d;
                color: #8b98a8;
                border: 1px solid #202b3a;
                padding: 7px 14px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: #111a26;
                color: #7fdfff;
                border-bottom: 2px solid #00d9ff;
            }

            QTabBar::tab:hover {
                background-color: #142333;
                color: #edf5ff;
            }

            /* ==================================================
            DM TRAIT TABLE
            ================================================== */

            QTableWidget {
                background-color: #080d14;
                alternate-background-color: #0d131d;
                border: 1px solid #202b3a;
                border-radius: 6px;
                color: #edf5ff;
                gridline-color: #1b2635;
                outline: none;
                selection-background-color: #087f98;
                selection-color: white;
            }

            QTableWidget::item {
                padding: 8px 10px;
                border: none;
            }

            QTableWidget::item:hover {
                background-color: #142333;
            }

            QTableWidget::item:selected {
                background-color: #087f98;
                color: white;
            }

            QHeaderView {
                background-color: #111a26;
            }

            QHeaderView::section {
                background-color: #111a26;
                border: none;
                border-right: 1px solid #202b3a;
                border-bottom: 1px solid #2a394d;
                color: #7fdfff;
                font-weight: 600;
                padding: 8px 10px;
            }

            /* ==================================================
            DM RESULTS
            ================================================== */

            QTextEdit#dmResults {
                background-color: #080d14;
                border: 1px solid #202b3a;
                border-radius: 6px;
                padding: 12px;
                color: #dbe8f5;
                font-family: "Segoe UI";
                font-size: 10pt;
                selection-background-color: #087f98;
                selection-color: white;
            }

            QTextEdit#dmResults h3 {
                color: #7fdfff;
            }

            /* ==================================================
            INPUT DIALOGS
            ================================================== */

            QInputDialog {
                background-color: #0d131d;
            }

            QInputDialog QLabel {
                background-color: transparent;
                color: #d9e2f0;
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QInputDialog QLineEdit,
            QInputDialog QComboBox,
            QInputDialog QDoubleSpinBox,
            QInputDialog QSpinBox {
                background-color: #111a26;
                border: 1px solid #2a394d;
                border-radius: 5px;
                padding: 7px 8px;
                color: #edf5ff;
                selection-background-color: #008fa8;
                selection-color: white;
            }

            QInputDialog QLineEdit:focus,
            QInputDialog QComboBox:focus,
            QInputDialog QDoubleSpinBox:focus,
            QInputDialog QSpinBox:focus {
                border: 1px solid #00d9ff;
            }

            QInputDialog QPushButton {
                background-color: #008fa8;
                border: none;
                border-radius: 6px;
                padding: 7px 12px;
                color: white;
                font-weight: 600;
                min-width: 55px;
            }

            QInputDialog QPushButton:hover {
                background-color: #00a9c7;
            }

            QInputDialog QPushButton:pressed {
                background-color: #00798f;
            }

            QLineEdit,
            QComboBox,
            QDoubleSpinBox,
            QSpinBox {
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
            QDoubleSpinBox:hover,
            QSpinBox:hover {
                border: 1px solid #3b5068;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDoubleSpinBox:focus,
            QSpinBox:focus {
                background-color: #121e2c;
                border: 1px solid #00d9ff;
            }

            /* ==================================================
            MESSAGE BOXES
            ================================================== */

            QMessageBox {
                background-color: #0d131d;
            }

            QMessageBox QLabel {
                background-color: transparent;
                color: #d9e2f0;
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QMessageBox QPushButton {
                background-color: #008fa8;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
                color: white;
                font-weight: 600;
                min-width: 70px;
            }

            QMessageBox QPushButton:hover {
                background-color: #00a9c7;
            }

            QMessageBox QPushButton:pressed {
                background-color: #00798f;
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