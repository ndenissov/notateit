from __future__ import annotations

__author__ = 'Nikita Denissov'

import sys
from argparse import ArgumentParser
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QScrollArea, QStatusBar, QMessageBox
)

from .parser import process_nat_file
from .renderer import render_slides
from .ui_components import SlideViewer, PresentationWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.close_action = None
        self.presentation_action = None
        self.setWindowTitle("Notateit Viewer Remake")
        self.setGeometry(100, 100, 1024, 768)
        self.slides_data = []
        self.current_slide_index = -1
        self.presentation_window = None

        self.slide_viewer = SlideViewer()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.slide_viewer)

        self.prev_button = QPushButton("Previous (Shift+P)")
        self.prev_button.setToolTip("Previous slide (Shift+P)")

        self.next_button = QPushButton("Next (Shift+N)")
        self.next_button.setToolTip("Next slide (Shift+N)")

        self.slide_label = QLabel("Open a .nat file to begin")
        self.slide_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.slide_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(nav_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setStatusBar(QStatusBar(self))
        self.create_menu_and_actions()

        self.prev_button.clicked.connect(self.prev_slide)
        self.next_button.clicked.connect(self.next_slide)
        self.update_ui_state()

    def create_menu_and_actions(self):
        prev_slide_action = QAction("Previous Slide", self)
        prev_slide_action.setShortcut(QKeySequence("Shift+P"))
        prev_slide_action.triggered.connect(self.prev_slide)
        self.addAction(prev_slide_action)

        next_slide_action = QAction("Next Slide", self)
        next_slide_action.setShortcut(QKeySequence("Shift+N"))
        next_slide_action.triggered.connect(self.next_slide)
        self.addAction(next_slide_action)

        minimize_action = QAction("Minimize Windows", self)
        minimize_action.setShortcut(QKeySequence("Esc"))
        minimize_action.triggered.connect(self.escape_app)
        self.addAction(minimize_action)

        menu_bar = self.menuBar()

        open_action = QAction("&Open (Ctrl+O)", self)
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        menu_bar.addAction(open_action)

        self.close_action = QAction("Close &File (Ctrl+X)", self)
        self.close_action.triggered.connect(self.close_file)
        self.close_action.setShortcut("Ctrl+X")
        menu_bar.addAction(self.close_action)

        self.presentation_action = QAction("&Presentation (F5)", self)
        self.presentation_action.triggered.connect(self.start_presentation)
        self.presentation_action.setShortcut(Qt.Key.Key_F5)
        menu_bar.addAction(self.presentation_action)

        self.addAction(self.presentation_action)

    def open_file(self, /, file_path_str=None):
        if not file_path_str:
            file_path_str, _ = QFileDialog.getOpenFileName(self, "Open Notabilia File", "", "NAT Files (*.nat)")
        if not file_path_str:
            return

        file_path = Path(file_path_str)
        self.statusBar().showMessage(f"Processing {file_path.name}...")
        QApplication.processEvents()

        try:
            doc_structure, _ = process_nat_file(file_path)
            self.statusBar().showMessage("Rendering slides...")
            QApplication.processEvents()
            self.slides_data = render_slides(doc_structure)
            if not self.slides_data:
                QMessageBox.warning(self, "Empty File", "No pages or objects found.")
                self.current_slide_index = -1
            else:
                self.current_slide_index = 0
            self.update_slide_view()
            self.statusBar().showMessage(f"Opened {file_path.name}. {len(self.slides_data)} slides found.", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open or process file:\n{e}")
            self.statusBar().showMessage("Failed to open file.", 5000)
            self.slides_data = []
            self.current_slide_index = -1
            self.update_ui_state()

    def close_file(self):
        QApplication.processEvents()
        self.slides_data = []
        self.current_slide_index = -1
        self.update_slide_view()
        self.update_ui_state()
        QApplication.processEvents()

    def update_slide_view(self):
        if 0 <= self.current_slide_index < len(self.slides_data):
            slide = self.slides_data[self.current_slide_index]
            self.slide_viewer.set_slide(slide['image'], slide['interactive_objects'])
            self.slide_label.setText(f"Slide {self.current_slide_index + 1} of {len(self.slides_data)}")
        else:
            bg_color = self.palette().color(self.backgroundRole())
            blank_image = Image.new('RGB', (1, 1), bg_color.toTuple())
            self.slide_viewer.set_slide(blank_image, [])
            self.slide_label.setText("Open a .nat file to begin")
        self.update_ui_state()

    def update_ui_state(self):
        has_slides = bool(self.slides_data)
        self.prev_button.setEnabled(has_slides and self.current_slide_index > 0)
        self.next_button.setEnabled(has_slides and self.current_slide_index < len(self.slides_data) - 1)
        self.presentation_action.setEnabled(has_slides)

    def prev_slide(self):
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self.update_slide_view()

    def next_slide(self):
        if self.current_slide_index < len(self.slides_data) - 1:
            self.current_slide_index += 1
            self.update_slide_view()

    def start_presentation(self):
        if not self.slides_data:
            return
        if self.presentation_window and self.presentation_window.isVisible():
            self.presentation_window.activateWindow()
            return
        self.presentation_window = PresentationWindow(self.slides_data)
        self.presentation_window.showFullScreen()
        self.presentation_window.go_to_slide(self.current_slide_index)

    def escape_app(self):
        if not self.slides_data and self.current_slide_index == -1:
            self.close()
            return
        self.showMinimized()


def get_icon_path() -> Path:
    filepath = Path('/usr/share/icons/hicolor/512x512/apps/notateit_remake.png')
    if filepath.is_file():
        return filepath
    filepath = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent), 'notateit_remake.png')
    if filepath.is_file():
        return filepath
    return Path(__file__).parent / 'notateit_remake.png'


def main():
    parser = ArgumentParser()
    parser.add_argument('input', nargs='?', help='Input .nat file path', type=Path)
    parser.add_argument('-x', '--extract', help='Extract .nat file', action='store_true')
    parser.add_argument('-o', '--output', help='Output assets and final .json file directory', type=Path)
    parser.add_argument('-m', '--minimize', help='Minimize the final .json file', action='store_true')
    args = parser.parse_args()
    input_path = args.input
    if args.extract:
        if not input_path:
            parser.print_help()
            exit(1)
        data, assets_dir = process_nat_file(input_path, assets_dir=args.output)
        output_path = assets_dir / f'{input_path.stem}.json'
        import json
        print(output_path)
        with open(output_path, 'w') as output_file:
            data = json.dumps(data, indent=1) if not args.minimize else json.dumps(data, separators=(',', ':'))
            output_file.write(data)
            print(f'Exported to {assets_dir}, saved to {output_path}')
        return
    app = QApplication(sys.argv)
    app_icon = QIcon(str(get_icon_path()))
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    app.setDesktopFileName("notateit.viewer.remake")
    window = MainWindow()
    window.show()
    if input_path is not None:
        window.open_file(file_path_str=input_path)
    sys.exit(app.exec())


"""
python3 -m nuitka --standalone --onefile --enable-plugin=pyside6 --output-dir=build --include-data-file=notateit/icon.png=icon.png main.py
"""
if __name__ == '__main__':
    main()
