#!/usr/bin/env python3
"""
AllTheTorr — Single-file GUI (PyQt5)
- Single-file: logic + GUI
- Dark theme, big list, search, sort, update URL, refresh, download (open magnet)
- Uses a background QThread for fetching uploads to avoid UI freeze
- Includes a dedicated Help window with tabs (FAQ, Shortcuts, Credits)
"""

import sys
import os
import json
import requests
import platform
import subprocess
import time
from urllib.parse import parse_qs, urlparse

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit, QTextBrowser,
    QSplitter, QFrame, QStatusBar, QMessageBox, QDialog, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# --------------------
# Configuration
# --------------------
DEFAULT_URL = "https://raw.githubusercontent.com/SabeeirSharrma/ATT-DB/main/uploads.json"
CONFIG_FILE = "config.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, dict) and "uploads_url" in data:
                return data
        except Exception:
            pass
    return {"uploads_url": DEFAULT_URL}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=4)
    except Exception:
        pass


# --------------------
# Logic functions (unchanged semantics)
# --------------------
def human_size_to_bytes(size_str):
    """Converts size strings (e.g., '3.5 GB', '450 MB') into MB-float for comparison."""
    if not size_str or size_str == "N/A":
        return 0.0
    size_str = size_str.upper().replace(",", "").strip()
    parts = size_str.split()
    if len(parts) != 2:
        # tolerate '3.5GB' or '450MB'
        if size_str.endswith("GB"):
            try:
                number = float(size_str.replace("GB", ""))
                unit = "GB"
            except Exception:
                return 0.0
        elif size_str.endswith("MB"):
            try:
                number = float(size_str.replace("MB", ""))
                unit = "MB"
            except Exception:
                return 0.0
        elif size_str.endswith("KB"):
            try:
                number = float(size_str.replace("KB", ""))
                unit = "KB"
            except Exception:
                return 0.0
        else:
            try:
                return float(size_str)
            except Exception:
                return 0.0
    else:
        try:
            number = float(parts[0])
            unit = parts[1]
        except Exception:
            return 0.0

    if "KB" in unit:
        return number / 1024.0
    elif "MB" in unit:
        return number
    elif "GB" in unit:
        return number * 1024.0
    elif "TB" in unit:
        return number * 1024.0 * 1024.0
    else:
        return 0.0


def search_uploads(upload_list, query):
    q = (query or "").lower().strip()
    if not q:
        return upload_list
    return [u for u in upload_list if q in u.get("title", "").lower()]


def open_magnet(magnet):
    """Open a magnet link in the default torrent client for current OS."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(magnet)
        elif system == "Darwin":
            subprocess.Popen(["open", magnet])
        else:
            subprocess.Popen(["xdg-open", magnet])
        return True, None
    except Exception as e:
        return False, str(e)


# --------------------
# Thread to fetch uploads (non-blocking for UI)
# --------------------
class FetchThread(QThread):
    finished_signal = pyqtSignal(list, str)  # uploads, error_message (empty if ok)

    def __init__(self, url, timeout=10):
        super().__init__()
        self.url = url
        self.timeout = timeout

    def run(self):
        try:
            r = requests.get(self.url, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                self.finished_signal.emit(data, "")
            else:
                # not an array -> error
                self.finished_signal.emit([], "JSON root is not a list")
        except Exception as e:
            self.finished_signal.emit([], str(e))


# --------------------
# Help Window (tabs)
# --------------------
class HelpWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AllTheTorr — Help")
        self.resize(640, 480)

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # FAQ tab
        faq = QTextBrowser()
        faq.setOpenExternalLinks(True)
        faq.setHtml(
            "<h2>FAQ</h2>"
            "<b>Q: How do I update the torrent database?</b><br>"
            "A: Enter a new raw JSON URL in the field and click <i>Update URL</i>.<br><br>"
            "<b>Q: How do I refresh the torrent list?</b><br>"
            "A: Click <i>Refresh DB</i> to reload the data.<br><br>"
            "<b>Q: Are all torrents legal?</b><br>"
            "A: This app is intended to display verified, legal torrents from the database.<br><br>"
            "<b>Q: Why won’t magnets open?</b><br>"
            "A: Ensure your torrent client is installed and set as the default handler for magnet links."
        )
        tabs.addTab(faq, "FAQ")

        # Shortcuts tab
        shortcuts = QTextBrowser()
        shortcuts.setHtml(
            "<h2>Shortcuts</h2>"
            "<b>Ctrl + F</b> — Focus search bar (if implemented)<br>"
            "<b>Enter</b> — Trigger search (when focus is in the search box)<br>"
            "<b>Ctrl + R</b> — Refresh database (not bound by default)<br>"
            "<b>Double-click item</b> — Download magnet (not bound by default)<br>"
        )
        tabs.addTab(shortcuts, "Shortcuts")

        # Credits tab
        credits = QTextBrowser()
        credits.setHtml(
            "<h2>Credits</h2>"
            "<b>AllTheTorr — GUI Edition</b><br><br>"
            "Developed by <b>Sabeeir Sharrma</b><br>"
            "UI improvements assisted by ChatGPT<br><br>"
            "This program is designed to distribute verified, legal torrents only."
        )
        tabs.addTab(credits, "Credits")

        # Dark styling for help dialog
        self.setStyleSheet("""
            QDialog { background: #121212; color: #e6e6e6; }
            QTabWidget::pane { border: 1px solid #333; }
            QTextBrowser { background: #181818; border: 1px solid #333; padding: 10px; }
            QTabBar::tab { background: #1f1f1f; padding: 8px; }
            QTabBar::tab:selected { background: #292929; }
        """)


# --------------------
# GUI (modernized)
# --------------------
class AllTheTorrGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AllTheTorr — GUI Edition")
        self.resize(1200, 700)
        self.setFont(QFont("Segoe UI", 10))

        # config + current uploads
        self.config = load_config()
        self.UPLOADS_URL = self.config.get("uploads_url", DEFAULT_URL)
        self.uploads = []  # list of dicts

        # Layout
        main = QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(8)

        # Controls grid (URL, update, refresh, search)
        controls = QGridLayout()
        controls.setHorizontalSpacing(8)
        controls.setVerticalSpacing(6)

        lbl_url = QLabel("Database URL:")
        self.input_url = QLineEdit(self.UPLOADS_URL)
        btn_update = QPushButton("Update URL")
        btn_refresh = QPushButton("Refresh DB")
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Search torrents...")
        btn_search = QPushButton("Search")
        btn_sort_small = QPushButton("Sort: Smallest")
        btn_sort_large = QPushButton("Sort: Largest")
        btn_help = QPushButton("Help")

        # place controls
        controls.addWidget(lbl_url, 0, 0)
        controls.addWidget(self.input_url, 0, 1, 1, 3)
        controls.addWidget(btn_update, 0, 4)
        controls.addWidget(btn_refresh, 0, 5)

        controls.addWidget(self.input_search, 1, 0, 1, 4)
        controls.addWidget(btn_search, 1, 4)
        controls.addWidget(btn_sort_small, 1, 5)
        controls.addWidget(btn_help, 0, 6)

        # extra spacing column stretch
        controls.setColumnStretch(1, 5)

        main.addLayout(controls)

        # Splitter: left (list) / right (info)
        splitter = QSplitter(Qt.Horizontal)

        # Left side widget
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(6)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(520)
        self.list_widget.setStyleSheet("font-size: 13px;")

        left_layout.addWidget(self.list_widget, stretch=1)

        # Right side widget
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(6)

        self.info_box = QTextBrowser()
        self.info_box.setOpenExternalLinks(True)
        self.info_box.setStyleSheet("padding:8px; font-size:13px; background:#1f1f1f;")
        self.info_box.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.btn_download = QPushButton("Download (Open Magnet)")
        self.btn_download.setFixedHeight(44)
        self.btn_download.setStyleSheet("font-size:13px;")

        right_layout.addWidget(self.info_box, stretch=1)
        right_layout.addWidget(self.btn_download)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 500])  # left larger by default

        main.addWidget(splitter, stretch=1)

        # Status bar
        self.status_bar = QStatusBar()
        main.addWidget(self.status_bar)

        # Apply dark stylesheet (pleasant default)
        self.setStyleSheet(""" 
            QWidget { background: #121212; color: #e6e6e6; }
            QLineEdit, QTextBrowser, QListWidget { background: #181818; color: #e6e6e6; border: 1px solid #2b2b2b; }
            QPushButton { background: #242424; color: #e6e6e6; border: 1px solid #2f2f2f; padding: 6px; border-radius:4px; }
            QPushButton:hover { background: #303030; }
            QStatusBar{ background: #0e0e0e; }
        """)

        # Wire signals
        btn_refresh.clicked.connect(self.on_refresh_clicked)
        btn_update.clicked.connect(self.on_update_url_clicked)
        btn_search.clicked.connect(self.on_search_clicked)
        btn_sort_small.clicked.connect(lambda: self.sort_by_size("smallest"))
        btn_sort_large.clicked.connect(lambda: self.sort_by_size("largest"))
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.btn_download.clicked.connect(self.on_download_clicked)
        btn_help.clicked.connect(self.show_help_window)

        # initial fetch (in background)
        self.fetch_thread = None
        self.start_fetch(self.UPLOADS_URL)

    # --------------------
    # Background fetch control
    # --------------------
    def start_fetch(self, url):
        self.set_controls_enabled(False)
        self.status_bar.showMessage("Fetching uploads...", 0)
        self.fetch_thread = FetchThread(url)
        self.fetch_thread.finished_signal.connect(self.on_fetch_finished)
        self.fetch_thread.start()

    def on_fetch_finished(self, uploads, error):
        # runs in GUI thread
        self.set_controls_enabled(True)
        if error:
            self.status_bar.showMessage(f"Failed to fetch: {error}", 6000)
            QMessageBox.critical(self, "Fetch error", f"Failed to fetch uploads:\n{error}")
            self.uploads = []
            self.populate_list([])
        else:
            self.uploads = uploads or []
            self.populate_list(self.uploads)
            self.status_bar.showMessage(f"Loaded {len(self.uploads)} torrents.", 4000)

        self.fetch_thread = None

    def set_controls_enabled(self, enable):
        # disable during fetching
        self.findChild(QLineEdit).setEnabled(enable)
        for w in self.findChildren(QPushButton):
            w.setEnabled(enable)

    # --------------------
    # Populate list
    # --------------------
    def populate_list(self, dataset):
        self.list_widget.clear()
        for item in dataset:
            title = item.get("title", "Untitled")
            size = item.get("size", "N/A")
            seeds = item.get("seeds", 0)
            text = f"{title}  |  {size}  |  Seeds: {seeds}"
            lw = QListWidgetItem(text)
            lw.setData(Qt.UserRole, item)
            self.list_widget.addItem(lw)

    # --------------------
    # Events
    # --------------------
    def on_refresh_clicked(self):
        self.start_fetch(self.UPLOADS_URL)

    def on_update_url_clicked(self):
        new_url = self.input_url.text().strip()
        if not new_url:
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid JSON URL.")
            return
        self.UPLOADS_URL = new_url
        self.config["uploads_url"] = new_url
        save_config(self.config)
        self.status_bar.showMessage("Database URL updated.", 3000)
        self.start_fetch(self.UPLOADS_URL)

    def on_search_clicked(self):
        q = self.input_search.text().strip()
        results = search_uploads(self.uploads, q)
        self.populate_list(results)
        self.status_bar.showMessage(f"Search results: {len(results)}", 3000)

    def sort_by_size(self, mode):
        if mode not in ("largest", "smallest"):
            return
        reverse_flag = (mode == "largest")
        try:
            sorted_list = sorted(self.uploads, key=lambda u: human_size_to_bytes(u.get("size", "0 MB")), reverse=reverse_flag)
            self.populate_list(sorted_list)
            self.status_bar.showMessage(f"Sorted by size ({mode})", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Sort error", f"Could not sort: {e}")

    def on_selection_changed(self):
        item = self.list_widget.currentItem()
        if not item:
            self.info_box.clear()
            return
        data = item.data(Qt.UserRole)
        desc = data.get("description", "")
        html = (
            f"<b>Title:</b> {data.get('title','')}<br>"
            f"<b>Description:</b><br>{desc}<br><br>"
            f"<b>Size:</b> {data.get('size','N/A')}<br>"
            f"<b>Seeds:</b> {data.get('seeds',0)}<br>"
            f"<b>Leeches:</b> {data.get('leeches',0)}<br><br>"
            f"<i>Click Download to open the magnet link in your torrent client.</i>"
        )
        self.info_box.setHtml(html)

    def on_download_clicked(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "No selection", "Please select a torrent to download.")
            return
        data = item.data(Qt.UserRole)
        magnet = data.get("magnet")
        if not magnet:
            QMessageBox.warning(self, "No magnet", "This entry has no magnet link.")
            return
        ok, err = open_magnet(magnet)
        if ok:
            self.status_bar.showMessage("Magnet opened in default torrent client.", 3000)
        else:
            QMessageBox.critical(self, "Open error", f"Failed to open magnet:\n{err}")

    # optional: allow double-click to open magnet
    def mouseDoubleClickEvent(self, ev):
        pass

    # --------------------
    # Help
    # --------------------
    def show_help_window(self):
        hw = HelpWindow(self)
        hw.exec_()


# --------------------
# Main
# --------------------
def main():
    app = QApplication(sys.argv)
    gui = AllTheTorrGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
