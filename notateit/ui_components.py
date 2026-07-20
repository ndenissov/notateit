__author__ = 'Nikita Denissov'

import os
import shutil

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QAction, QMouseEvent, QShortcut, QKeySequence
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QMenu, QFileDialog, QMessageBox, QApplication, QDialog,
    QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton
)
from PySide6.QtWidgets import (QWidget, QLabel, QSizePolicy)


class TextViewerDialog(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Text")

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(True)

        copy_button = QPushButton("Copy All")
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.text_edit.toPlainText()))

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(copy_button)
        btn_layout.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        layout.addLayout(btn_layout)
        self.resize(500, 400)


class InteractiveObjectWidget(QPushButton):
    """Interactive object (text or image)"""

    def __init__(self, obj_data, parent=None):
        super().__init__(parent)
        self.obj_data = obj_data

        self.setStyleSheet("QPushButton{background-color:transparent;border:none;}"
                           "QPushButton:focus{border:2px solid #0078d7;}")

        obj_type = self.obj_data['data']['type']
        value = self.obj_data['data']['value']
        if obj_type == 'Text':
            self.setToolTip(f'Text Block\n'
                            f'- Double-click or Ctrl+Enter to open\n'
                            f'- Ctrl+C to copy\n'
                            f'"{value}"')
        elif obj_type == 'Image':
            self.setToolTip(f'{value} Block\n'
                            f'- Double-click or Ctrl+Enter to open\n'
                            f'- Ctrl+S to save')

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.shortcut_open = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_open.activated.connect(self.do_default_action)

        self.shortcut_copy = QShortcut(QKeySequence("Ctrl+C"), self)
        self.shortcut_copy.activated.connect(
            lambda: self.copy_text(self.obj_data['data'])
            if self.obj_data['data']['type'] == 'Text' else None
        )

        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(
            lambda: self.save_image_as(self.obj_data['data'])
            if self.obj_data['data']['type'] == 'Image' else None
        )

        self._set_shortcuts_enabled(False)

    def focusInEvent(self, event):
        self._set_shortcuts_enabled(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._set_shortcuts_enabled(False)
        super().focusOutEvent(event)

    def _set_shortcuts_enabled(self, enabled: bool):
        self.shortcut_open.setEnabled(enabled)
        self.shortcut_copy.setEnabled(enabled)
        self.shortcut_save.setEnabled(enabled)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.do_default_action()
        super().mouseDoubleClickEvent(event)

    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        obj_type = self.obj_data['data']['type']

        if obj_type == 'Text':
            view_action = QAction("&Open Text...", self)
            view_action.setShortcut("Ctrl+Enter")
            view_action.triggered.connect(lambda: self.view_text_content(self.obj_data['data']))
            menu.addAction(view_action)

            copy_action = QAction("&Copy Text", self)
            copy_action.setShortcut("Ctrl+C")
            copy_action.triggered.connect(lambda: self.copy_text(self.obj_data['data']))
            menu.addAction(copy_action)

        elif obj_type == 'Image':
            show_action = QAction("&Open Image", self)
            show_action.setShortcut("Ctrl+Enter")
            show_action.triggered.connect(lambda: self.show_image(self.obj_data['data']))
            menu.addAction(show_action)

            save_as_action = QAction("&Save Image As...", self)
            save_as_action.setShortcut("Ctrl+S")
            save_as_action.triggered.connect(lambda: self.save_image_as(self.obj_data['data']))
            menu.addAction(save_as_action)

        menu.exec(self.mapToGlobal(pos))

    def do_default_action(self):
        obj_type = self.obj_data['data']['type']
        if obj_type == 'Text':
            self.view_text_content(self.obj_data['data'])
        elif obj_type == 'Image':
            self.show_image(self.obj_data['data'])

    def view_text_content(self, text_data):
        dialog = TextViewerDialog(text_data['value'], self)
        dialog.exec()

    def copy_text(self, text_data):
        QApplication.clipboard().setText(text_data['value'])
        if hasattr(self.window(), 'statusBar'):
            self.window().statusBar().showMessage("Text copied to clipboard", 2000)

    def show_image(self, image_data):
        try:
            Image.open(image_data['file']).show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open image:\n{e}")

    def save_image_as(self, image_data):
        source_path = image_data['file']
        filename = os.path.basename(source_path)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Image As...", filename, "Images (*.png *.jpg);;All Files (*)"
        )
        if path:
            try:
                shutil.copy(source_path, path)
                QMessageBox.information(self, "Success", f"Image saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save image:\n{e}")


class SlideViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_label = QLabel(self)
        self.background_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.background_label.move(0, 0)
        self.overlay_widgets = []

    def set_slide(self, pil_image: Image, objects: list):
        for widget in self.overlay_widgets:
            widget.deleteLater()
        self.overlay_widgets.clear()

        qim = ImageQt(pil_image.convert("RGBA"))
        pixmap = QPixmap.fromImage(qim)

        self.background_label.setPixmap(pixmap)
        self.background_label.adjustSize()

        for obj in objects:
            overlay = InteractiveObjectWidget(obj, self.background_label)
            overlay.setGeometry(obj['rect'])
            overlay.show()
            self.overlay_widgets.append(overlay)

        self.setMinimumSize(self.background_label.size())
        self.updateGeometry()


class PresentationWindow(QWidget):
    def __init__(self, slides_data, parent=None):
        super().__init__(parent)
        self.slides_data = slides_data
        self.current_index = -1
        self.current_pixmap = QPixmap()
        self.slide_label = QLabel(self)
        self.slide_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slide_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.slide_label)
        self.setWindowTitle("Presentation Mode")
        self.setStyleSheet("background-color: black;")

    def go_to_slide(self, index):
        if not (0 <= index < len(self.slides_data)): return
        if self.current_index != index:
            self.current_index = index
            pil_image = self.slides_data[self.current_index]['image']
            qim = ImageQt(pil_image.convert("RGBA"))
            self.current_pixmap = QPixmap.fromImage(qim)
        self._update_display()

    def _update_display(self):
        if self.current_pixmap.isNull(): return
        scaled_pixmap = self.current_pixmap.scaled(
            self.slide_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.slide_label.setPixmap(scaled_pixmap)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Right, Qt.Key.Key_Space, Qt.Key.Key_PageDown):
            self.go_to_slide(self.current_index + 1)
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            self.go_to_slide(self.current_index - 1)
        elif key == Qt.Key.Key_Escape:
            self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()
