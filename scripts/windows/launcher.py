"""Vitalcer Headless Desktop Launcher & Service Orchestrator.

Supervises background services (PostgreSQL, FastAPI backend, Caddy) and browser
launching for non-technical users with zero console popups.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0


def get_app_root() -> Path:
    """Resolve base directory for frozen executable or source repository."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.3) -> bool:
    """Check if TCP port is actively accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def start_postgres(app_root: Path) -> None:
    """Start local PostgreSQL cluster cleanly if not already running."""
    if is_port_open(5432):
        return
    pg_ctl = (
        app_root
        / "tools"
        / "pgsql"
        / "bin"
        / ("pg_ctl.exe" if IS_WINDOWS else "pg_ctl")
    )
    if not pg_ctl.is_file():
        system_pg = shutil.which("pg_ctl")
        if not system_pg:
            return
        pg_ctl = Path(system_pg)

    data_dir = app_root / "data" / "postgres"
    logs_dir = app_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(pg_ctl),
        "-D",
        str(data_dir),
        "-l",
        str(logs_dir / "postgres.log"),
        "-w",
        "start",
    ]
    subprocess.run(
        cmd,
        creationflags=CREATE_NO_WINDOW,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def start_backend(app_root: Path) -> None:
    """Start the FastAPI backend server headlessly."""
    if is_port_open(8000):
        return
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    if getattr(sys, "frozen", False):
        cmd = [str(sys.executable), "--backend"]
    else:
        cmd = [sys.executable, str(Path(__file__).resolve()), "--backend"]

    proc = subprocess.Popen(
        cmd,
        cwd=str(app_root),
        env=env,
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pid_file = app_root / "data" / "logs" / "backend.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(proc.pid), encoding="utf-8")


def start_caddy(app_root: Path) -> None:
    """Start the Caddy reverse proxy and static SPA web server."""
    if is_port_open(5174):
        return
    caddy_exe = app_root / "tools" / "caddy" / ("caddy.exe" if IS_WINDOWS else "caddy")
    if not caddy_exe.is_file():
        system_caddy = shutil.which("caddy")
        if not system_caddy:
            return
        caddy_exe = Path(system_caddy)

    cmd = [str(caddy_exe), "run", "--config", str(app_root / "Caddyfile")]
    subprocess.Popen(
        cmd,
        cwd=str(app_root),
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def start_all(app_root: Path) -> None:
    """Start Postgres, Backend, and Caddy, waiting briefly for port binding."""
    start_postgres(app_root)
    start_backend(app_root)
    start_caddy(app_root)
    for _ in range(25):
        if is_port_open(5174) and is_port_open(8000) and is_port_open(5432):
            break
        time.sleep(0.2)


def stop_all(app_root: Path) -> None:
    """Stop all running background services cleanly."""
    if IS_WINDOWS:
        subprocess.run(
            ["taskkill.exe", "/F", "/IM", "caddy.exe"],
            creationflags=CREATE_NO_WINDOW,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    pid_file = app_root / "data" / "logs" / "backend.pid"
    if pid_file.is_file():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            if IS_WINDOWS:
                subprocess.run(
                    ["taskkill.exe", "/F", "/PID", str(pid)],
                    creationflags=CREATE_NO_WINDOW,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                os.kill(pid, 15)
        except Exception:
            pass
        finally:
            pid_file.unlink(missing_ok=True)

    pg_ctl = (
        app_root
        / "tools"
        / "pgsql"
        / "bin"
        / ("pg_ctl.exe" if IS_WINDOWS else "pg_ctl")
    )
    if not pg_ctl.is_file():
        system_pg = shutil.which("pg_ctl")
        if system_pg:
            pg_ctl = Path(system_pg)
    if pg_ctl.is_file():
        data_dir = app_root / "data" / "postgres"
        subprocess.run(
            [str(pg_ctl), "-D", str(data_dir), "-m", "fast", "stop"],
            creationflags=CREATE_NO_WINDOW,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def run_backend_server() -> None:
    """Execute FastAPI application inside Uvicorn."""
    import uvicorn

    from server.main import app

    host = os.environ.get("VITALCER_HOST", "0.0.0.0")
    port = int(os.environ.get("VITALCER_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")


def main() -> None:
    app_root = get_app_root()
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "--pos"

    if arg in ("--backend", "--server"):
        run_backend_server()
        return

    if arg in ("--startup", "--start-all", "--start"):
        start_all(app_root)
        return

    if arg == "--stop":
        stop_all(app_root)
        return

    if arg == "--admin":
        start_all(app_root)
        webbrowser.open("https://localhost:5173")
        return

    start_all(app_root)
    webbrowser.open("https://localhost:5174")


if __name__ == "__main__":
    main()
