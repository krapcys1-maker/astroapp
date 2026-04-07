from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from app.config.settings import AppSettings


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings
        self.setWindowTitle("astroapp")
        self.resize(960, 640)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("astroapp")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Desktop astrology workspace bootstrap")
        subtitle.setObjectName("subtitleLabel")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.setCentralWidget(root)