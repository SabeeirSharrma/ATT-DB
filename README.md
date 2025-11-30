# 📁 AllTheTorr

**AllTheTorr** is a friendly open-source torrent database browser featuring both CLI (Command Line Interface) and GUI (Graphical User Interface) modes. It empowers users to interact with torrent databases hosted in JSON format and let their community easily browse, search, and download torrents via magnet links—automatically opening in their preferred torrent client (such as qBittorrent or uTorrent).

---

## 👀 Features

- **Custom Torrent Databases:**  
  Create and share your own torrent databases in JSON format. Host them anywhere accessible (GitHub, web server, etc.).

- **CLI Tool:**  
  Intuitive text-based interface for searching and managing torrents from any terminal.

- **GUI Application:**  
  Modern, easy-to-use desktop interface built with PyQt5 for seamless browsing and searching.

- **Database Flexibility:**  
  Switch between different database URLs at any time within both the CLI and GUI.

- **Rich Torrent Info:**  
  Display detailed information about each torrent—title, description, size, seeds, leeches, verification status, trackers, and web seeds.

- **Built-in Magnet Link Handling:**  
  Download torrents instantly; the application will open the magnet link in your default torrent client.

- **Sorting and Filtering:**  
  Quickly sort torrents by size (ascending/descending) and search by title.

---

## ❓ How Does It Work?

1. **Database Format:**  
   - Torrents are listed in a `.json` file, each entry containing details (title, description, size, seeds, leeches, magnet, etc.).
   - Host your database file (e.g. on GitHub or any direct URL).
   - [Sample json file](https://github.com/SabeeirSharrma/ATT-DB/main/README.md#example-database-entry)
   

2. **Interact with Torrents:**  
   - Enter or select the database URL in the application.
   - Browse, search, and sort the available torrents.
   - When you choose to download, the app opens the magnet link via your system’s default torrent client.

3. **CLI & GUI:**  
   - Both interfaces support the core browsing and downloading functionality.
   - Switch the database URL any time.

---

## ▶️ How to Run

1. **Windows Executables (Recommended for Windows Users)**
   If you have the executables, running the application is simple:

   | Interface | Executable Command | Description |
   | --------- | ------------------ | ----------- |
   | **GUI**   | `AllTheTorr.exe`   | Launches the interactive graphical window for easy browsing and downloading. |
   | **CLI**   | `ATT_CLI.exe`      | Launches the command-line interface for terminal interaction. |
   
2. **Python Scripts (For Mac and Linux Users)**
   You can run the desired interface directly from the terminal (after installing dependencies).
   `pip install rich requests pyqt5`

   - For CLI:
     `python CLI.py`
     
   - For GUI:
     `python GUI.py`

---

## ⏬ Downloading Torrents

- **For CLI:**
  By using the `list` command you will see the complete list of torrents on the database along with their designated IDs.
  Use the `download` command and then a small prompt will appear requesting torrent ID, enter torrent ID and it will automatically open your default torrenting app with the magnet link pre-set.
  
- **For GUI:**
  Choose you designated torrent from the list and click on the download button, it will automatically open your default torrenting app with the magnet link pre-set.
  
---

## 📅 Using Your Own Database

  Edit the `config.json` with your database URL, or set it via the application's controls.

  - For CLI:
    Do `seturl` and a prompt `Enter new JSON database URL:` will appear under it, enter the new URL and database will refresh.

  - For GUI:
    Enter new URL in place of old one and click update URL.

---

## 💲 CLI Commands

| Command       | Description   |
| ------------- |:-------------:|
| `list`        | Displays the current torrent database in a formatted table. |
| `sort`        | Prompts for the sort direction (largest/smallest) to display torrents sorted by size. |
| `seturl`      | Change Database URL (updates config.json). |
| `download`    | Prompts for a Torrent ID and opens the magnet link instantly. |
| `info`        | Prompts for a Torrent ID to display detailed information. |
| `search`      | Prompts for a query string to filter torrents by title. |
| `refresh`     | Fetches the latest data from the configured database URL. |
| `exit`        | Closes the CLI. |

---
## ❓ Example Database Entry

```json
[
  {
    "id": "T001",
    "title": "Ubuntu ISO",
    "description": "Official Ubuntu 22.04 LTS image.",
    "size": "3.2 GB",
    "seeds": 340,
    "leeches": 24,
    "magnet": "magnet:?xt=urn:btih:...",
    "verified": true
  },
  ...
]
```

---

## ❓ FAQ

- **Q:** How do I create my own database?  
  **A:** Make a JSON file with the format shown above, upload it to a public hosting service or GitHub, and set its URL in the app.

- **Q:** Will it work with any torrent client?  
  **A:** Yes, any torrent client that supports magnet links.

- **Q:** Is my database private?  
  **A:** Only if you control its hosting URL; otherwise anyone with the URL can access it.

---

## 📩 Contributing

Pull requests and suggestions welcome! Feel free to fork the repository and propose improvements.

---

## 🙌 License

GNU AGPL License

---

** 💻 Created by [SabeeirSharrma](https://github.com/SabeeirSharrma)**
