import os
from datetime import datetime
from pathlib import Path


def get_output_root() -> str:
    return os.getenv("OUTPUT_ROOT", "BulkImageGen")


def make_output_dir(client_name: str) -> str:
    slug = slugify_client(client_name)
    dt = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(get_output_root()) / slug / dt / "images"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def make_run_dir(client_name: str) -> str:
    """Returns the run root (parent of images/) for placing report.xlsx."""
    slug = slugify_client(client_name)
    dt = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(get_output_root()) / slug / dt
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def slugify_client(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "client"


def ensure_data_dir() -> None:
    Path("data").mkdir(exist_ok=True)


def open_folder(path: str) -> None:
    import subprocess, sys
    if sys.platform == "win32":
        subprocess.Popen(["explorer", os.path.abspath(path)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
