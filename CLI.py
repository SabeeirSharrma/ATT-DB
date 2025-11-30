import json
import requests
import os
import platform
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlparse
from rich.console import Console
from rich.table import Table
from rich.spinner import Spinner
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich import box
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.style import Style


CONFIG_FILE = "config.json"
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)

            # Auto-fix old/broken configs that are lists
            if isinstance(data, list):
                return {"uploads_url": DEFAULT_UPLOADS_URL}

            # Correct format
            if isinstance(data, dict):
                return data

        except Exception:
            pass

    # If file missing or corrupted
    return {"uploads_url": DEFAULT_UPLOADS_URL}


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)


console = Console()

DEFAULT_UPLOADS_URL = "https://raw.githubusercontent.com/SabeeirSharrma/ATT-DB/main/uploads.json"
config = load_config()
UPLOADS_URL = config.get("uploads_url", DEFAULT_UPLOADS_URL)

def ascii_progress(task="Working", duration=1.8, length=20, color="\033[38;5;46m"):
    """Show a simple colored ASCII progress bar."""
    start = time.time()
    RESET = "\033[38;5;46m"

    while True:
        elapsed = time.time() - start
        progress = min(elapsed / duration, 1.0)

        filled = int(progress * length)
        bar = "#" * filled + "-" * (length - filled)
        percent = int(progress * 100)

        sys.stdout.write(
            f"\r{task}: {color}[{bar}] {percent}%{RESET}"
        )
        sys.stdout.flush()

        if progress >= 1.0:
            break
        
        time.sleep(0.05)

    sys.stdout.write("\n")


# ----------------------------
# Fetch JSON with Rich Spinner
# ----------------------------
def fetch_uploads():
    ascii_progress("Fetching uploads", duration=2.0, color="\033[38;5;46m")  # GREEN

    try:
        response = requests.get(UPLOADS_URL, timeout=10)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        console.print(f"[red]Failed to fetch uploads:[/red] {e}")
        return []


# ----------------------------
# List Torrents as Table
# ----------------------------
def list_uploads(uploads, sort_by=None):
    # Apply sorting if requested
    if sort_by == "size":
        console.print("[yellow]Sorting by Size (Ascending)...[/yellow]")
        # Sort using the helper function
        uploads.sort(key=lambda u: human_size_to_bytes(u.get("size", "0 B")), reverse=False)
        
    elif sort_by == "size_desc":
        console.print("[yellow]Sorting by Size (Descending)...[/yellow]")
        uploads.sort(key=lambda u: human_size_to_bytes(u.get("size", "0 B")), reverse=True)


    table = Table(
        title="AllTheTorr Database",
        box=box.ROUNDED,
        border_style="cyan"
    )
    # ... (rest of the table setup remains the same)
    table.add_column("ID", style="yellow", overflow="fold")
    table.add_column("Title", style="bold")
    table.add_column("Size", justify="right", style="cyan")
    table.add_column("Seeds", justify="right", style="green")
    table.add_column("Leeches", justify="right", style="red")
    
    console.print("\n[bold red]!!PLEASE SEED THE TORRENTS TO SUPPORT THE UPLOADERS!![/bold red]\n")

    for u in uploads:
        table.add_row(
            u["id"],
            u["title"],
            u["size"],
            str(u["seeds"]),
            str(u["leeches"])
        )

    console.print(table)


# ----------------------------
# Search Torrents
# ----------------------------
def search_uploads(uploads, query):
    return [u for u in uploads if query.lower() in u['title'].lower()]


# ----------------------------
# Magnet Opener
# ----------------------------
def open_magnet(magnet):
    system = platform.system()

    try:
        if system == "Windows":
            os.startfile(magnet)
        elif system == "Darwin":
            subprocess.Popen(["open", magnet])
        else:
            subprocess.Popen(["xdg-open", magnet])

        console.print("[bold green]✔ Magnet opened in your default torrent client.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to open magnet: {e}[/bold red]")


# ----------------------------
# Parse Magnet: Extract trackers & webseeds
# ----------------------------
def parse_magnet(magnet):
    parsed = urlparse(magnet)
    params = parse_qs(parsed.query)

    trackers = params.get("tr", [])
    webseeds = params.get("ws", [])

    return trackers, webseeds


# ----------------------------
# Torrent Info Viewer (Popout)
# ----------------------------
def show_info(torrent):
    trackers, webseeds = parse_magnet(torrent["magnet"])

    verified = "[green]✔ Verified[/green]" if torrent.get("verified") else "[red]✘ Not Verified[/red]"

    # --- Details Table ---
    details = Table.grid(expand=True)
    details.add_column(justify="left")
    details.add_column(justify="right")

    details.add_row("[bold cyan]Title[/bold cyan]", torrent["title"])
    details.add_row("[cyan]Description[/cyan]", torrent["description"])
    details.add_row("[cyan]Size[/cyan]", torrent["size"])
    details.add_row("[cyan]Seeds[/cyan]", str(torrent["seeds"]))
    details.add_row("[cyan]Leeches[/cyan]", str(torrent["leeches"]))
    details.add_row("[cyan]Verified[/cyan]", verified)

    # --- Trackers table ---
    tracker_table = None
    if trackers:
        tracker_table = Table(title="Trackers", box=box.SIMPLE)
        tracker_table.add_column("URL", style="magenta", overflow="fold")
        for t in trackers:
            tracker_table.add_row(t)

    # --- Web Seeds table ---
    ws_table = None
    if webseeds:
        ws_table = Table(title="Web Seeds", box=box.SIMPLE)
        ws_table.add_column("URL", style="yellow", overflow="fold")
        for w in webseeds:
            ws_table.add_row(w)

    # --- Build layout grid ---
    layout = Table.grid(expand=True)
    layout.add_row(details)
    layout.add_row("\n[bold blue]Magnet Link:[/bold blue]\n" + torrent["magnet"])
    layout.add_row(tracker_table if tracker_table else "[dim]No trackers listed[/dim]")
    layout.add_row(ws_table if ws_table else "[dim]No web seeds listed[/dim]")
    layout.add_row("\n[bold green] Use Download option to start downloading[/bold green]\n")

    # --- Wrap in Panel ---
    panel = Panel(
        layout,
        title=f"[bold green]Torrent Info — {torrent['id']}[/bold green]",
        border_style="green",
        padding=(1, 2)
    )

    console.print(panel)


# -----------------------------------------------------------------------
# Helper function to convert human-readable size to a comparable number
# -----------------------------------------------------------------------
def human_size_to_bytes(size_str):
    """Converts a human-readable size string (e.g., '10.5 GB') to a float for sorting."""
    if not size_str or size_str == "N/A":
        return 0.0

    size_str = size_str.upper().replace(",", "")
    
    # Simple regex to extract number and unit
    parts = size_str.split()
    if len(parts) != 2:
        # Handle cases like '100 MB' (no space) or just a number
        if size_str.endswith("GB"):
             number = float(size_str.replace("GB", ""))
             unit = "GB"
        elif size_str.endswith("MB"):
             number = float(size_str.replace("MB", ""))
             unit = "MB"
        elif size_str.endswith("KB"):
             number = float(size_str.replace("KB", ""))
             unit = "KB"
        else:
             try:
                 return float(size_str) # Assume bytes if no unit
             except ValueError:
                 return 0.0
    else:
        number = float(parts[0])
        unit = parts[1]

    
    if "KB" in unit:
        return number / 1024.0 # Convert to MB
    elif "MB" in unit:
        return number
    elif "GB" in unit:
        return number * 1024.0 # Convert to MB
    elif "TB" in unit:
        return number * 1024.0 * 1024.0 # Convert to MB
    else:
        return 0.0 # Default if unit is unrecognized

 # ----------------
# Main Program Loop
# ----------------- 
def main():
    uploads = fetch_uploads()
    if not uploads:
        return

    while True:
        cmd = Prompt.ask(
            "\n[cyan]Enter command[/cyan]",
            choices=["list", "search", "info", "download", "refresh", "sort", "seturl", "exit"],
            default="list"
        )

        if cmd == "list":
            # Pass no sort argument (default)
            list_uploads(uploads)

        elif cmd == "sort":
            sortby= Prompt.ask(
                "[magenta]Sort by size (largest/smallest)[/magenta]",
                choices=["smallest", "largest"],
                default="largest"
                )

            if sortby == "largest":
                list_uploads(uploads, sort_by="size_desc")
            elif sortby == "smallest":
                list_uploads(uploads, sort_by="size")
            
        elif cmd == "search":
            q = Prompt.ask("[yellow]Search for[/yellow]")
            results = search_uploads(uploads, q)
            if results:
                # Note: Search results are not sorted by default here
                list_uploads(results) 
            else:
                console.print("[red]No results found.[/red]")

        # ... (rest of the main function remains the same: info, download, refresh, exit)
        elif cmd == "info":
            tid = Prompt.ask("[magenta]Enter torrent ID[/magenta]")
            found = next((u for u in uploads if u["id"] == tid), None)
            if not found:
                console.print("[red]❌ Invalid ID[/red]")
                continue
            show_info(found)

        elif cmd == "download":
            tid = Prompt.ask("[magenta]Enter torrent ID[/magenta]")
            found = next((u for u in uploads if u["id"] == tid), None)

            if not found:
                console.print("[red]❌ Torrent ID not found.[/red]")
                continue

            console.print("\n[bold red]!!PLEASE SEED THE TORRENTS TO SUPPORT THE UPLOADERS!![/bold red]\n")
            ascii_progress("Opening magnet", duration=1.6)
            open_magnet(found["magnet"])

        elif cmd == "refresh":
            uploads = fetch_uploads()
            console.print("[green]✔ Database refreshed[/green]")
            

        elif cmd == "exit":
            console.print("[bold cyan]Goodbye![/bold cyan]")
            break

        elif cmd == "seturl":
            new_url = Prompt.ask("[bold yellow]Enter new JSON database URL[/bold yellow]")
            config["uploads_url"] = new_url
            save_config(config)

            global UPLOADS_URL
            UPLOADS_URL = new_url

            console.print(f"[bold green]✔ Database URL updated to {new_url}![/bold green]")

            ascii_progress("Fetching uploads...", duration=2.0)
            uploads = fetch_uploads()


if __name__ == "__main__":
    main()
