import sys
import os
import json
import requests
import platform
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QTextEdit,
    QMessageBox, QSplitter, QFileDialog
)
from PyQt5.QtCore import Qt

DEFAULT_URL = "https://raw.githubusercontent.com/SabeeirSharrma/ATT-DB/main/uploads.json"
CONFIG_FILE = "config.json"

# --------------------------
# Config Handling
# --------------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, dict) and "uploads_url" in data:
                return data
        except:
            pass
    return {"uploads_url": DEFAULT_URL}


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)


# --------------------------
# Size Conversion
# --------------------------
def human_size_to_bytes(size_str):
    if not size_str or size_str == "N/A":
        return 0.0
    size_str = size_str.upper().replace(",", "")
    parts = size_str.split()
    if len(parts) != 2:
        if size_str.endswith("GB"):
            number = float(size_str.replace("GB", "")); unit = "GB"
        elif size_str.endswith("MB"):
            number = float(size_str.replace("MB", "")); unit = "MB"
        elif size_str.endswith("KB"):
            number = float(size_str.replace("KB", "")); unit = "KB"
        else:
            try: return float(size_str)
            except: return 0.0
    else:
        number = float(parts[0]); unit = parts[1]

    if "KB" in unit: return number / 1024.0
    if "MB" in unit: return number
    if "GB" in unit: return number * 1024.0
    if "TB" in unit: return number * 1024.0 * 1024.0
    return 0.0


# --------------------------
# Magnet opener
# --------------------------
def open_magnet(magnet):
    system = platform.system()
    try:
        if system == "Windows": os.startfile(magnet)
        elif system == "Darwin": subprocess.Popen(["open", magnet])
        else: subprocess.Popen(["xdg-open", magnet])
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to open magnet: {e}")


# --------------------------
# Main GUI
# --------------------------
class TorrentGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AllTheTorr — GUI Edition")
        self.resize(1000, 600)

        self.config = load_config()
        self.uploads_url = self.config["uploads_url"]
        self.uploads = []

        self.layout = QHBoxLayout(self)
        self.left_panel = QVBoxLayout()
        self.right_panel = QVBoxLayout()

        # URL + Refresh Controls
        self.url_label = QLabel("Database URL:")
        self.url_edit = QLineEdit(self.uploads_url)
        self.btn_seturl = QPushButton("Update URL")
        self.btn_refresh = QPushButton("Refresh DB")

        url_box = QHBoxLayout()
        url_box.addWidget(self.url_edit)
        url_box.addWidget(self.btn_seturl)
        url_box.addWidget(self.btn_refresh)

        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search torrents...")
        self.btn_search = QPushButton("Search")
        search_box = QHBoxLayout()
        search_box.addWidget(self.search_edit)
        search_box.addWidget(self.btn_search)

        # Sort buttons
        self.btn_sort_small = QPushButton("Sort: Smallest")
        self.btn_sort_large = QPushButton("Sort: Largest")
        sort_box = QHBoxLayout()
        sort_box.addWidget(self.btn_sort_small)
        sort_box.addWidget(self.btn_sort_large)

        # List widget
        self.list = QListWidget()
        self.list.setMinimumHeight(500)

        self.left_panel.addWidget(self.url_label)
        self.left_panel.addLayout(url_box)
        self.left_panel.addLayout(search_box)
        self.left_panel.addLayout(sort_box)
        self.left_panel.addWidget(self.list, stretch=100)

        # Right panel (info)
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)

        self.btn_download = QPushButton("Download (Open Magnet)")

        self.right_panel.addWidget(self.info_box)
        self.right_panel.addWidget(self.btn_download)

        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget(); left_widget.setLayout(self.left_panel)
        right_widget = QWidget(); right_widget.setLayout(self.right_panel)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)  # Left panel gets priority
        splitter.setStretchFactor(1, 0)  # Right panel stays fixed


        self.layout.addWidget(splitter)

        self.btn_refresh.clicked.connect(self.load_uploads)
        self.btn_seturl.clicked.connect(self.update_url)
        self.btn_search.clicked.connect(self.run_search)
        self.list.itemClicked.connect(self.show_info)
        self.btn_download.clicked.connect(self.download_selected)
        self.btn_sort_small.clicked.connect(lambda: self.sort_by_size("smallest"))
        self.btn_sort_large.clicked.connect(lambda: self.sort_by_size("largest"))

        self.load_uploads()

    # ----------------------
    # Load database
    # ----------------------
    def load_uploads(self):
        try:
            r = requests.get(self.uploads_url, timeout=10)
            r.raise_for_status()
            self.uploads = r.json()
            self.populate_list(self.uploads)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch uploads: {e}")

    def populate_list(self, dataset):
        self.list.clear()
        for item in dataset:
            lw = QListWidgetItem(f"{item['title']}  |  {item['size']}  |  Seeds: {item['seeds']}")
            lw.setData(Qt.UserRole, item)
            self.list.addItem(lw)

    # ----------------------
    # Searching
    # ----------------------
    def run_search(self):
        q = self.search_edit.text().lower().strip()
        if not q:
            self.populate_list(self.uploads)
            return
        results = [u for u in self.uploads if q in u['title'].lower()]
        self.populate_list(results)

    # ----------------------
    # Show info on right side
    # ----------------------
    def show_info(self, item):
        data = item.data(Qt.UserRole)
        txt = (
            f"<b>Title:</b> {data['title']}<br>"
            f"<b>Description:</b> {data['description']}<br><br>"
            f"<b>Size:</b> {data['size']}<br>"
            f"<b>Seeds:</b> {data['seeds']}<br>"
            f"<b>Leeches:</b> {data['leeches']}<br>"
            
        )
        self.info_box.setHtml(txt)

    # ----------------------
    # Sort
    # ----------------------
    def sort_by_size(self, mode):
        reverse_flag = mode == "largest"
        sorted_list = sorted(self.uploads, key=lambda u: human_size_to_bytes(u['size']), reverse=reverse_flag)
        self.populate_list(sorted_list)

    # ----------------------
    # Download
    # ----------------------
    def download_selected(self):
        item = self.list.currentItem()
        if not item:
            QMessageBox.warning(self, "No selection", "Please select a torrent first.")
            return
        data = item.data(Qt.UserRole)
        open_magnet(data["magnet"])

    # ----------------------
    # Change DB URL
    # ----------------------
    def update_url(self):
        new_url = self.url_edit.text().strip()
        if not new_url:
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL.")
            return
        self.uploads_url = new_url
        self.config["uploads_url"] = new_url
        save_config(self.config)
        self.load_uploads()
        QMessageBox.information(self, "Updated", "Database URL updated!")


# --------------------------
# Run App
# --------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = TorrentGUI()
    gui.show()
    sys.exit(app.exec_())
