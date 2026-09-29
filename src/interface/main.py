import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QBrush,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QDockWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QLineEdit,
    QToolBar,
    QMenu,
    QMenuBar,
    QStatusBar,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QSplitter,
    QFrame,
    QSizePolicy,
    QTreeWidgetItemIterator,
)


# ============================================================
# COLORS / THEME
# ============================================================

BG = "#181818"
PANEL = "#202020"
PANEL2 = "#242424"
PANEL3 = "#292929"
BORDER = "#333333"
TEXT = "#D6D6D6"
TEXT_DIM = "#929292"
ACCENT = "#4C9AFF"
ACCENT_HOVER = "#65A9FF"
SELECTED = "#31465D"
INPUT = "#151515"


# ============================================================
# ICON GENERATOR
# ============================================================

def make_icon(symbol, color=TEXT, size=16):
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    font = QFont("Segoe UI Symbol", int(size * 0.75))
    painter.setFont(font)
    painter.setPen(QColor(color))

    painter.drawText(
        pixmap.rect(),
        Qt.AlignCenter,
        symbol
    )

    painter.end()

    return QIcon(pixmap)


# ============================================================
# VIEWPORT
# ============================================================

class Viewport(QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumSize(500, 400)
        self.setMouseTracking(True)

        self.grid_size = 40

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # ----------------------------------------------------
        # Background
        # ----------------------------------------------------

        painter.fillRect(self.rect(), QColor("#171717"))

        w = self.width()
        h = self.height()

        # ----------------------------------------------------
        # Grid
        # ----------------------------------------------------

        pen = QPen(QColor("#242424"))
        pen.setWidth(1)
        painter.setPen(pen)

        spacing = self.grid_size

        for x in range(0, w, spacing):
            painter.drawLine(x, 0, x, h)

        for y in range(0, h, spacing):
            painter.drawLine(0, y, w, y)

        # ----------------------------------------------------
        # Center axes
        # ----------------------------------------------------

        pen_x = QPen(QColor("#7A3434"))
        pen_x.setWidth(2)

        pen_y = QPen(QColor("#3D7A48"))
        pen_y.setWidth(2)

        center_x = w // 2
        center_y = h // 2

        painter.setPen(pen_x)
        painter.drawLine(center_x, center_y, w, center_y)

        painter.setPen(pen_y)
        painter.drawLine(center_x, center_y, center_x, 0)

        # ----------------------------------------------------
        # Origin
        # ----------------------------------------------------

        painter.setBrush(QBrush(QColor(ACCENT)))
        painter.setPen(Qt.NoPen)

        painter.drawEllipse(
            center_x - 5,
            center_y - 5,
            10,
            10
        )

        # ----------------------------------------------------
        # Axis labels
        # ----------------------------------------------------

        painter.setPen(QColor("#777777"))
        painter.setFont(QFont("Segoe UI", 9))

        painter.drawText(
            center_x + 10,
            center_y - 10,
            "X"
        )

        painter.drawText(
            center_x + 10,
            20,
            "Y"
        )

        # ----------------------------------------------------
        # Viewport overlay
        # ----------------------------------------------------

        painter.setPen(QColor("#777777"))
        painter.setFont(QFont("Segoe UI", 10))

        painter.drawText(
            15,
            25,
            "Scene View"
        )

        painter.drawText(
            15,
            45,
            "Perspective"
        )

        painter.drawText(
            15,
            h - 20,
            "LMB Orbit   •   MMB Pan   •   Wheel Zoom"
        )

        painter.end()


# ============================================================
# HIERARCHY
# ============================================================

class HierarchyWidget(QWidget):

    def __init__(self, inspector):
        super().__init__()

        self.inspector = inspector

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        self.search.setClearButtonEnabled(True)

        layout.addWidget(self.search)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(18)

        layout.addWidget(self.tree)

        self.populate()

        self.tree.itemClicked.connect(
            self.object_selected
        )

        self.search.textChanged.connect(
            self.filter_items
        )

    def populate(self):

        scene = QTreeWidgetItem(["🌐  Scene"])

        self.tree.addTopLevelItem(scene)

        camera = QTreeWidgetItem(["📷  Main Camera"])
        light = QTreeWidgetItem(["☀  Directional Light"])
        rover = QTreeWidgetItem(["🚙  Rover"])

        wheel_fl = QTreeWidgetItem(["◉  Front Left Wheel"])
        wheel_fr = QTreeWidgetItem(["◉  Front Right Wheel"])
        wheel_rl = QTreeWidgetItem(["◉  Rear Left Wheel"])
        wheel_rr = QTreeWidgetItem(["◉  Rear Right Wheel"])

        rover.addChildren([
            wheel_fl,
            wheel_fr,
            wheel_rl,
            wheel_rr,
        ])

        scene.addChildren([
            camera,
            light,
            rover,
        ])

        scene.setExpanded(True)
        rover.setExpanded(True)

        self.tree.expandAll()

    def object_selected(self, item, column):

        name = item.text(0)

        self.inspector.set_object(name)

    def filter_items(self, text):

        text = text.lower()

        iterator = QTreeWidgetItemIterator(self.tree)

        while iterator.value():

            item = iterator.value()

            item.setHidden(
                text not in item.text(0).lower()
            )

            iterator += 1


# ============================================================
# INSPECTOR
# ============================================================

class Inspector(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(
            10, 10, 10, 10
        )

        self.layout.setSpacing(8)

        self.title = QLabel("Inspector")
        self.title.setObjectName("InspectorTitle")

        self.layout.addWidget(self.title)

        self.object_name = QLabel("Nothing selected")

        self.layout.addWidget(
            self.object_name
        )

        self.create_transform()

        self.layout.addStretch()

    def create_transform(self):

        group = QGroupBox("Transform")

        form = QFormLayout(group)

        self.position_x = self.spin()
        self.position_y = self.spin()
        self.position_z = self.spin()

        self.rotation_x = self.spin()
        self.rotation_y = self.spin()
        self.rotation_z = self.spin()

        self.scale_x = self.spin(1)
        self.scale_y = self.spin(1)
        self.scale_z = self.spin(1)

        form.addRow("Position X", self.position_x)
        form.addRow("Position Y", self.position_y)
        form.addRow("Position Z", self.position_z)

        form.addRow("Rotation X", self.rotation_x)
        form.addRow("Rotation Y", self.rotation_y)
        form.addRow("Rotation Z", self.rotation_z)

        form.addRow("Scale X", self.scale_x)
        form.addRow("Scale Y", self.scale_y)
        form.addRow("Scale Z", self.scale_z)

        self.layout.addWidget(group)

        # ----------------------------------------------------
        # Mesh renderer
        # ----------------------------------------------------

        renderer = QGroupBox("Mesh Renderer")

        renderer_layout = QVBoxLayout(renderer)

        material = QComboBox()

        material.addItems([
            "Default Material",
            "Metal",
            "Plastic",
            "Glass",
        ])

        renderer_layout.addWidget(
            QLabel("Material")
        )

        renderer_layout.addWidget(
            material
        )

        cast_shadow = QCheckBox(
            "Cast Shadows"
        )

        cast_shadow.setChecked(True)

        renderer_layout.addWidget(
            cast_shadow
        )

        self.layout.addWidget(renderer)

    def spin(self, value=0):

        spin = QDoubleSpinBox()

        spin.setRange(
            -1000000,
            1000000
        )

        spin.setDecimals(3)

        spin.setSingleStep(0.1)

        spin.setValue(value)

        return spin

    def set_object(self, name):

        self.object_name.setText(name)


# ============================================================
# PROJECT / ASSET BROWSER
# ============================================================

class ProjectWidget(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            8, 8, 8, 8
        )

        search = QLineEdit()
        search.setPlaceholderText(
            "Search assets..."
        )

        layout.addWidget(search)

        self.assets = QListWidget()

        assets = [
            ("📁", "Scenes"),
            ("📁", "Materials"),
            ("📁", "Meshes"),
            ("📁", "Textures"),
            ("📁", "Scripts"),
            ("📁", "Prefabs"),
            ("🌍", "Earth.scene"),
            ("🚀", "Rover.prefab"),
            ("📷", "Camera.prefab"),
        ]

        for icon, name in assets:

            item = QListWidgetItem(
                f"{icon}  {name}"
            )

            self.assets.addItem(item)

        layout.addWidget(
            self.assets
        )


# ============================================================
# CONSOLE
# ============================================================

class ConsoleWidget(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            5, 5, 5, 5
        )

        self.output = QPlainTextEdit()

        self.output.setReadOnly(True)

        self.output.appendPlainText(
            "[INFO] Application started."
        )

        self.output.appendPlainText(
            "[INFO] Simulation engine initialized."
        )

        self.output.appendPlainText(
            "[INFO] GPU renderer initialized."
        )

        layout.addWidget(
            self.output
        )

    def log(self, message):

        self.output.appendPlainText(
            message
        )


# ============================================================
# TIMELINE
# ============================================================

class Timeline(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            10, 5, 10, 5
        )

        # Transport controls

        self.play = QPushButton("▶")
        self.pause = QPushButton("Ⅱ")
        self.stop = QPushButton("■")

        for button in [
            self.play,
            self.pause,
            self.stop,
        ]:

            button.setFixedSize(35, 28)

            layout.addWidget(button)

        # Time

        self.time = QLabel(
            "00:00:00.000"
        )

        layout.addWidget(
            self.time
        )

        layout.addStretch()

        layout.addWidget(
            QLabel("Frame")
        )

        self.frame = QSpinBox()

        self.frame.setRange(
            0,
            1000000
        )

        layout.addWidget(
            self.frame
        )

        layout.addWidget(
            QLabel("FPS")
        )

        fps = QLabel("60")

        layout.addWidget(fps)


# ============================================================
# DOCK CREATOR
# ============================================================

def create_dock(
    parent,
    title,
    widget,
    area
):

    dock = QDockWidget(
        title,
        parent
    )

    dock.setWidget(widget)

    dock.setAllowedAreas(
        Qt.AllDockWidgetAreas
    )

    dock.setFeatures(
        QDockWidget.DockWidgetMovable
        | QDockWidget.DockWidgetFloatable
        | QDockWidget.DockWidgetClosable
    )

    parent.addDockWidget(
        area,
        dock
    )

    return dock


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Orbital Studio"
        )

        self.resize(
            1600,
            950
        )

        self.setMinimumSize(
            1100,
            700
        )

        self.console = ConsoleWidget()

        self.inspector = Inspector()

        self.create_menu()

        self.create_toolbar()

        self.create_viewport()

        self.create_panels()

        self.create_status_bar()

        self.setup_connections()

    # ========================================================
    # MENU
    # ========================================================

    def create_menu(self):

        menu = self.menuBar()

        file_menu = menu.addMenu("File")

        new_action = QAction(
            "New Scene",
            self
        )

        open_action = QAction(
            "Open Scene...",
            self
        )

        save_action = QAction(
            "Save Scene",
            self
        )

        exit_action = QAction(
            "Exit",
            self
        )

        exit_action.triggered.connect(
            self.close
        )

        file_menu.addAction(
            new_action
        )

        file_menu.addAction(
            open_action
        )

        file_menu.addAction(
            save_action
        )

        file_menu.addSeparator()

        file_menu.addAction(
            exit_action
        )

        # ----------------------------------------------------

        edit_menu = menu.addMenu("Edit")

        edit_menu.addAction(
            "Undo"
        )

        edit_menu.addAction(
            "Redo"
        )

        edit_menu.addSeparator()

        edit_menu.addAction(
            "Preferences..."
        )

        # ----------------------------------------------------

        view_menu = menu.addMenu("View")

        view_menu.addAction(
            "Scene"
        )

        view_menu.addAction(
            "Game"
        )

        view_menu.addAction(
            "Inspector"
        )

        view_menu.addAction(
            "Console"
        )

        # ----------------------------------------------------

        simulation = menu.addMenu(
            "Simulation"
        )

        simulation.addAction(
            "Play"
        )

        simulation.addAction(
            "Pause"
        )

        simulation.addAction(
            "Stop"
        )

        simulation.addSeparator()

        simulation.addAction(
            "Simulation Settings..."
        )

        # ----------------------------------------------------

        tools = menu.addMenu(
            "Tools"
        )

        tools.addAction(
            "Orbit Calculator"
        )

        tools.addAction(
            "Trajectory Generator"
        )

        tools.addAction(
            "SPICE Browser"
        )

        # ----------------------------------------------------

        help_menu = menu.addMenu(
            "Help"
        )

        help_menu.addAction(
            "Documentation"
        )

        help_menu.addAction(
            "About"
        )

    # ========================================================
    # TOOLBAR
    # ========================================================

    def create_toolbar(self):

        toolbar = QToolBar(
            "Main Toolbar"
        )

        toolbar.setMovable(False)

        toolbar.setIconSize(
            QSize(18, 18)
        )

        self.addToolBar(
            toolbar
        )

        # ----------------------------------------------------
        # File controls
        # ----------------------------------------------------

        new = QAction(
            "New",
            self
        )

        toolbar.addAction(
            new
        )

        open_action = QAction(
            "Open",
            self
        )

        toolbar.addAction(
            open_action
        )

        save = QAction(
            "Save",
            self
        )

        toolbar.addAction(
            save
        )

        toolbar.addSeparator()

        # ----------------------------------------------------
        # Transform tools
        # ----------------------------------------------------

        select = QAction(
            "Select",
            self
        )

        move = QAction(
            "Move",
            self
        )

        rotate = QAction(
            "Rotate",
            self
        )

        scale = QAction(
            "Scale",
            self
        )

        toolbar.addAction(
            select
        )

        toolbar.addAction(
            move
        )

        toolbar.addAction(
            rotate
        )

        toolbar.addAction(
            scale
        )

        toolbar.addSeparator()

        # ----------------------------------------------------
        # Play controls
        # ----------------------------------------------------

        self.play_action = QAction(
            "▶",
            self
        )

        self.pause_action = QAction(
            "Ⅱ",
            self
        )

        self.stop_action = QAction(
            "■",
            self
        )

        toolbar.addAction(
            self.play_action
        )

        toolbar.addAction(
            self.pause_action
        )

        toolbar.addAction(
            self.stop_action
        )

        toolbar.addSeparator()

        # ----------------------------------------------------
        # Layout button
        # ----------------------------------------------------

        layout_action = QAction(
            "Reset Layout",
            self
        )

        toolbar.addAction(
            layout_action
        )

        layout_action.triggered.connect(
            self.reset_layout
        )

    # ========================================================
    # VIEWPORT
    # ========================================================

    def create_viewport(self):

        self.viewport = Viewport()

        self.setCentralWidget(
            self.viewport
        )

    # ========================================================
    # PANELS
    # ========================================================

    def create_panels(self):

        # Hierarchy
        self.hierarchy = HierarchyWidget(
            self.inspector
        )

        self.hierarchy_dock = create_dock(
            self,
            "Hierarchy",
            self.hierarchy,
            Qt.LeftDockWidgetArea
        )

        # Inspector
        self.inspector_dock = create_dock(
            self,
            "Inspector",
            self.inspector,
            Qt.RightDockWidgetArea
        )

        # Project
        self.project = ProjectWidget()

        self.project_dock = create_dock(
            self,
            "Project",
            self.project,
            Qt.BottomDockWidgetArea
        )

        # Console
        self.console_dock = create_dock(
            self,
            "Console",
            self.console,
            Qt.BottomDockWidgetArea
        )

        # Timeline
        self.timeline = Timeline()

        self.timeline_dock = create_dock(
            self,
            "Timeline",
            self.timeline,
            Qt.BottomDockWidgetArea
        )

        # ----------------------------------------------------
        # Arrange bottom docks
        # ----------------------------------------------------

        self.resizeDocks(
            [
                self.hierarchy_dock,
                self.inspector_dock,
                self.project_dock,
                self.console_dock,
                self.timeline_dock,
            ],
            [
                260,
                300,
                250,
                250,
                250,
            ],
            Qt.Horizontal
        )

    # ========================================================
    # STATUS BAR
    # ========================================================

    def create_status_bar(self):

        status = QStatusBar()

        self.setStatusBar(
            status
        )

        status.showMessage(
            "Ready"
        )

        gpu = QLabel(
            "GPU  12%"
        )

        cpu = QLabel(
            "CPU  8%"
        )

        fps = QLabel(
            "FPS 60"
        )

        status.addPermanentWidget(
            cpu
        )

        status.addPermanentWidget(
            gpu
        )

        status.addPermanentWidget(
            fps
        )

    # ========================================================
    # CONNECTIONS
    # ========================================================

    def setup_connections(self):

        self.play_action.triggered.connect(
            lambda:
            self.console.log(
                "[SIM] Simulation started."
            )
        )

        self.pause_action.triggered.connect(
            lambda:
            self.console.log(
                "[SIM] Simulation paused."
            )
        )

        self.stop_action.triggered.connect(
            lambda:
            self.console.log(
                "[SIM] Simulation stopped."
            )
        )

        self.timeline.play.clicked.connect(
            lambda:
            self.console.log(
                "[SIM] Playing..."
            )
        )

        self.timeline.pause.clicked.connect(
            lambda:
            self.console.log(
                "[SIM] Paused."
            )
        )

        self.timeline.stop.clicked.connect(
            lambda:
            self.console.log(
                "[SIM] Stopped."
            )
        )

    # ========================================================
    # RESET LAYOUT
    # ========================================================

    def reset_layout(self):

        self.removeDockWidget(
            self.hierarchy_dock
        )

        self.removeDockWidget(
            self.inspector_dock
        )

        self.removeDockWidget(
            self.project_dock
        )

        self.removeDockWidget(
            self.console_dock
        )

        self.removeDockWidget(
            self.timeline_dock
        )

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.hierarchy_dock
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.inspector_dock
        )

        self.addDockWidget(
            Qt.BottomDockWidgetArea,
            self.project_dock
        )

        self.addDockWidget(
            Qt.BottomDockWidgetArea,
            self.console_dock
        )

        self.addDockWidget(
            Qt.BottomDockWidgetArea,
            self.timeline_dock
        )


# ============================================================
# GLOBAL STYLE
# ============================================================

STYLE = f"""

QMainWindow {{
    background: {BG};
    color: {TEXT};
}}

QMenuBar {{
    background: {PANEL};
    color: {TEXT};
    border-bottom: 1px solid {BORDER};
    padding: 2px;
}}

QMenuBar::item {{
    padding: 5px 10px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background: {PANEL3};
}}

QMenu {{
    background: {PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
}}

QMenu::item {{
    padding: 7px 30px 7px 20px;
}}

QMenu::item:selected {{
    background: {SELECTED};
}}

QToolBar {{
    background: {PANEL};
    border: none;
    border-bottom: 1px solid {BORDER};
    spacing: 4px;
    padding: 4px;
}}

QToolButton {{
    color: {TEXT};
    background: transparent;
    border: 1px solid transparent;
    padding: 5px 8px;
}}

QToolButton:hover {{
    background: {PANEL3};
    border: 1px solid {BORDER};
}}

QToolButton:pressed {{
    background: {SELECTED};
}}

QDockWidget {{
    color: {TEXT};
    background: {PANEL};
    titlebar-close-icon: none;
}}

QDockWidget::title {{
    background: {PANEL2};
    padding: 7px;
    border-bottom: 1px solid {BORDER};
    font-weight: bold;
}}

QTreeWidget {{
    background: {PANEL};
    color: {TEXT};
    border: none;
    outline: none;
}}

QTreeWidget::item {{
    padding: 5px;
}}

QTreeWidget::item:hover {{
    background: {PANEL3};
}}

QTreeWidget::item:selected {{
    background: {SELECTED};
    color: white;
}}

QListWidget {{
    background: {PANEL};
    color: {TEXT};
    border: none;
}}

QListWidget::item {{
    padding: 6px;
}}

QListWidget::item:hover {{
    background: {PANEL3};
}}

QListWidget::item:selected {{
    background: {SELECTED};
}}

QLineEdit {{
    background: {INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 6px;
}}

QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}

QGroupBox {{
    color: {TEXT};
    border: 1px solid {BORDER};
    margin-top: 10px;
    padding-top: 12px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}}

QDoubleSpinBox,
QSpinBox,
QComboBox {{
    background: {INPUT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px;
}}

QDoubleSpinBox:focus,
QSpinBox:focus,
QComboBox:focus {{
    border: 1px solid {ACCENT};
}}

QPushButton {{
    background: {PANEL3};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 12px;
}}

QPushButton:hover {{
    background: #333333;
}}

QPushButton:pressed {{
    background: {SELECTED};
}}

QPlainTextEdit {{
    background: #121212;
    color: #BDBDBD;
    border: none;
    font-family: Consolas;
    font-size: 10pt;
}}

QStatusBar {{
    background: {PANEL};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
}}

QLabel {{
    color: {TEXT};
}}

QScrollBar:vertical {{
    background: {PANEL};
    width: 10px;
}}

QScrollBar::handle:vertical {{
    background: #3A3A3A;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: #4A4A4A;
}}

QSplitter::handle {{
    background: {BORDER};
}}

QCheckBox {{
    color: {TEXT};
}}

"""

# ============================================================
# MAIN
# ============================================================

def main():

    app = QApplication(sys.argv)
    app.setStyle(
        "Fusion"
    )
    app.setStyleSheet(
        STYLE
    )
    
    window = MainWindow()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
