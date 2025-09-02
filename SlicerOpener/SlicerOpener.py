from __future__ import annotations

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import configparser
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs, unquote

try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    tk = None
    messagebox = None


@dataclass
class SlicerDefinition:
    display_name: str
    executable_path: str
    supported_extensions: list[str]


class SlicerOpenerError(Exception):
    pass


def get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_config(config_path: str):
    parser = configparser.ConfigParser()
    if not parser.read(config_path):
        raise SlicerOpenerError(f"Configuration file not found at {config_path}")
    if not parser.has_section("main"):
        raise SlicerOpenerError("[main] section missing in config.ini")
    storage_base = parser.get("main", "AUTHORITATIVE_STORAGE_BASE_PATH", fallback=None)
    if storage_base:
        storage_base = storage_base.strip().strip('"').strip("'")
    if not storage_base:
        raise SlicerOpenerError("AUTHORITATIVE_STORAGE_BASE_PATH is required in [main]")
    log_path = parser.get("main", "LOG_PATH", fallback=os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "SlicerOpener", "sliceropener.log"))
    slicers: list[SlicerDefinition] = []
    for section in parser.sections():
        if section == "main" or not section.lower().startswith("slicer_"):
            continue
        name = parser.get(section, "name", fallback=None)
        path = parser.get(section, "path", fallback=None)
        if path:
            path = path.strip().strip('"').strip("'")
        exts = [e.strip().lower() for e in parser.get(section, "extensions", fallback="").split(",") if e.strip()]
        if name and path and exts:
            slicers.append(SlicerDefinition(name, path, exts))
    if not slicers:
        raise SlicerOpenerError("No slicers configured. Add [slicer_*] sections with name, path, extensions.")
    return storage_base, log_path, slicers


def setup_logger(log_path: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger("SlicerOpener")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger


def show_error(title: str, message: str) -> None:
    if messagebox is None:
        print(f"ERROR: {title}: {message}")
        return
    root = tk.Tk(); root.withdraw(); messagebox.showerror(title, message); root.destroy()


def show_info(title: str, message: str) -> None:
    if messagebox is None:
        print(f"INFO: {title}: {message}")
        return
    root = tk.Tk(); root.withdraw(); messagebox.showinfo(title, message); root.destroy()


def parse_protocol_url(url_arg: str) -> str:
    url_str = url_arg.strip().strip('"')
    lower = url_str.lower()
    if "://" not in lower:
        raise SlicerOpenerError("Invalid URL scheme. Expected print3d://")
    scheme = lower.split("://", 1)[0]
    if scheme != "print3d":
        raise SlicerOpenerError("Invalid URL scheme. Expected print3d://")
    # Replace scheme with http for parsing
    tail = url_str[url_str.lower().find("://") + 3:]
    surrogate = "http://" + tail
    parsed = urlparse(surrogate)
    raw_path = parse_qs(parsed.query).get("path", [None])[0]
    if not raw_path:
        raise SlicerOpenerError("Missing 'path' parameter in URL.")
    return os.path.normpath(unquote(raw_path))


def validate_requested_path(file_path: str, storage_base: str) -> None:
    norm = lambda p: os.path.realpath(os.path.normcase(os.path.normpath(p)))
    base = norm(storage_base); target = norm(file_path)
    try:
        common = os.path.commonpath([base, target])
    except ValueError:
        raise SlicerOpenerError("Requested path is on a different drive than storage base.")
    if common != base:
        raise SlicerOpenerError("Requested path is not under the configured storage base. Check drive mapping and config.ini.")
    if not os.path.exists(target):
        raise SlicerOpenerError("Requested file does not exist. Ensure the network share is connected.")


def find_compatible_slicers(file_path: str, slicers: list[SlicerDefinition]) -> list[SlicerDefinition]:
    ext = os.path.splitext(file_path)[1].lower()
    return [s for s in slicers if ext in s.supported_extensions]


def launch_slicer(slicer: SlicerDefinition, file_path: str, logger: logging.Logger) -> None:
    if not os.path.exists(slicer.executable_path):
        raise SlicerOpenerError(f"Slicer executable not found: {slicer.executable_path}. Update path in config.ini.")
    logger.info("Launching slicer '%s' at '%s' with file '%s'", slicer.display_name, slicer.executable_path, file_path)
    try:
        subprocess.Popen([slicer.executable_path, file_path], shell=False)
    except Exception as e:
        raise SlicerOpenerError(f"Failed to launch slicer: {e}")


def main() -> int:
    app_dir = get_app_dir()
    config_path = os.path.join(app_dir, "config.ini")
    # Load config and logger
    try:
        storage_base, log_path, slicers = load_config(config_path)
        logger = setup_logger(log_path)
    except Exception as e:
        # Best-effort logger
        logger = setup_logger(os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "SlicerOpener", "sliceropener.log"))
        logger.error("Failed to load config: %s", e)
        show_error("Configuration Error", str(e))
        return 1

    try:
        if len(sys.argv) < 2:
            raise SlicerOpenerError("No URL argument provided by the protocol handler.")
        url_arg = sys.argv[1]
        logger.info("Received URL: %s", url_arg)
        file_path = parse_protocol_url(url_arg)
        # If the provided path is relative, resolve it under storage_base.
        # Special-case common pattern where relative path starts with 'storage/' and
        # storage_base already ends with 'storage' to avoid double 'storage/storage'.
        if not os.path.isabs(file_path):
            rel = file_path.replace('/', os.sep).replace('\\', os.sep)
            base_leaf = os.path.basename(os.path.normpath(storage_base)).lower()
            if rel.lower().startswith(base_leaf + os.sep):
                rel = rel.split(os.sep, 1)[1] if os.sep in rel else ''
            file_path = os.path.join(storage_base, rel)
        logger.info("Resolved file path: %s", file_path)
        validate_requested_path(file_path, storage_base)
        logger.info("Path validation OK. Base: %s", storage_base)
        compatible = find_compatible_slicers(file_path, slicers)
        if not compatible:
            raise SlicerOpenerError(f"No compatible slicer configured for '{os.path.splitext(file_path)[1].lower()}'. Update config.ini.")
        chosen = compatible[0]
        if len(compatible) > 1 and tk is not None:
            # Simple chooser
            selection: dict[str, SlicerDefinition | None] = {"value": None}
            def on_ok():
                idxs = listbox.curselection(); selection["value"] = compatible[idxs[0]] if idxs else None; window.destroy()
            def on_cancel():
                selection["value"] = None; window.destroy()
            window = tk.Tk(); window.title("Choose slicer"); window.geometry("360x240"); window.resizable(False, False)
            tk.Label(window, text="Select a slicer to open this file:").pack(padx=12, pady=(12,6))
            listbox = tk.Listbox(window, height=min(8, len(compatible)))
            for s in compatible: listbox.insert(tk.END, s.display_name)
            listbox.pack(fill=tk.BOTH, expand=True, padx=12, pady=6); listbox.selection_set(0)
            btns = tk.Frame(window); btns.pack(pady=(6,12))
            tk.Button(btns, text="OK", width=10, command=on_ok).pack(side=tk.LEFT, padx=6)
            tk.Button(btns, text="Cancel", width=10, command=on_cancel).pack(side=tk.LEFT, padx=6)
            window.mainloop()
            if selection["value"] is None:
                logger.info("User cancelled slicer selection dialog.")
                return 0
            chosen = selection["value"]
        launch_slicer(chosen, file_path, logger)
        show_info("Success", f"Opened file in {chosen.display_name}:\n{file_path}")
        logger.info("Launched '%s' for '%s'", chosen.display_name, file_path)
        return 0
    except SlicerOpenerError as e:
        logger.error("%s", e)
        show_error("SlicerOpener", str(e))
        return 2
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        show_error("Unexpected Error", str(e))
        return 3


if __name__ == "__main__":
    sys.exit(main())


