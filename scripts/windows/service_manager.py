"""Vitalcer Process Supervisor & Service Manager.

Manages the core Vitalcer services (PostgreSQL, FastAPI backend, Caddy reverse
proxy) with process lifecycle controls, socket health checks, log capturing,
and LAN IP discovery. Compatible with Windows and POSIX environments.
"""

from __future__ import annotations

import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Callable, Optional

IS_WINDOWS = platform.system() == "Windows"
if sys.platform == "win32":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "postgres"
LOGS_DIR = REPO_ROOT / "data" / "logs"


class ServiceProcess:
    """Represents a supervised managed background service."""

    def __init__(
        self,
        name: str,
        display_name: str,
        port: int,
        start_cmd: list[str],
        env: Optional[dict[str, str]] = None,
        working_dir: Optional[Path] = None,
        log_buffer_size: int = 500,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.port = port
        self.start_cmd = start_cmd
        self.env = env or {}
        self.working_dir = working_dir or REPO_ROOT
        self.process: Optional[subprocess.Popen[str]] = None
        self.logs: deque[str] = deque(maxlen=log_buffer_size)
        self.log_callbacks: list[Callable[[str], None]] = []
        self._reader_thread: Optional[threading.Thread] = None
        self.is_external: bool = False

    def add_log_listener(self, callback: Callable[[str], None]) -> None:
        self.log_callbacks.append(callback)

    def _append_log(self, line: str) -> None:
        clean = line.rstrip("\r\n")
        self.logs.append(clean)
        for cb in self.log_callbacks:
            try:
                cb(clean)
            except Exception:
                pass

    def is_port_open(self, host: str = "127.0.0.1", timeout: float = 0.4) -> bool:
        """Check if service port is currently accepting TCP connections."""
        try:
            with socket.create_connection((host, self.port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def is_running(self) -> bool:
        if self.is_external:
            return self.is_port_open()
        if self.process is not None:
            if self.process.poll() is None:
                return True
            self.process = None
        return self.is_port_open()

    def start(self) -> bool:
        """Start the service process if not already running."""
        if self.is_running():
            self._append_log(
                f"[{self.display_name}] Ya está en ejecución en puerto {self.port}."
            )
            return True

        merged_env = os.environ.copy()
        merged_env.update(self.env)

        self._append_log(
            f"[{self.display_name}] Iniciando servicio ({' '.join(self.start_cmd)})..."
        )
        try:
            creationflags = 0
            if IS_WINDOWS:
                creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

            self.process = subprocess.Popen(
                self.start_cmd,
                cwd=str(self.working_dir),
                env=merged_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags,
            )

            self._reader_thread = threading.Thread(
                target=self._stream_output,
                daemon=True,
            )
            self._reader_thread.start()

            # Wait briefly for process or port to bind
            for _ in range(25):
                time.sleep(0.2)
                if self.is_port_open():
                    self._append_log(
                        f"[{self.display_name}] Activo en puerto {self.port} ✅"
                    )
                    return True
                if self.process and self.process.poll() is not None:
                    code = self.process.returncode
                    if code == 0:
                        for _ in range(25):
                            time.sleep(0.2)
                            if self.is_port_open():
                                self._append_log(
                                    f"[{self.display_name}] Activo en puerto {self.port} ✅"
                                )
                                return True
                    self._append_log(
                        f"[{self.display_name}] Proceso terminó código {code} ❌"
                    )
                    self.process = None
                    return False

            if self.is_running():
                return True
            self._append_log(
                f"[{self.display_name}] Aviso: puerto {self.port} aún no responde."
            )
            return True
        except Exception as e:
            self._append_log(f"[{self.display_name}] Error al iniciar: {e} ❌")
            self.process = None
            return False

    def _stream_output(self) -> None:
        if not self.process or not self.process.stdout:
            return
        try:
            for line in self.process.stdout:
                self._append_log(f"[{self.name}] {line}")
        except Exception:
            pass

    def stop(self) -> bool:
        """Stop the managed service cleanly."""
        if self.is_external:
            self._append_log(
                f"[{self.display_name}] Servicio externo (no administrado)."
            )
            return True

        if not self.process:
            return True

        self._append_log(f"[{self.display_name}] Deteniendo servicio...")
        try:
            if IS_WINDOWS:
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGTERM)

            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
            self.process = None
            self._append_log(f"[{self.display_name}] Servicio detenido. ⏹️")
            return True
        except Exception as e:
            self._append_log(f"[{self.display_name}] Error al detener: {e}")
            return False


class ServiceManager:
    """Coordinates PostgreSQL, FastAPI Backend, and Caddy Web Server."""

    def __init__(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.python_cmd = self._find_python_command()
        self.caddy_cmd = self._find_caddy_command()
        self.postgres_cmd = self._find_postgres_command()

        self.services: dict[str, ServiceProcess] = {}
        self._init_services()

    def _find_python_command(self) -> list[str]:
        uv_path = shutil.which("uv")
        if uv_path:
            return ["uv", "run"]
        return [sys.executable, "-m"]

    def _find_caddy_command(self) -> str:
        local_caddy = (
            REPO_ROOT / "tools" / "caddy" / ("caddy.exe" if IS_WINDOWS else "caddy")
        )
        if local_caddy.is_file():
            return str(local_caddy)
        system_caddy = shutil.which("caddy")
        if system_caddy:
            return system_caddy
        return "caddy"

    def _find_postgres_command(self) -> Optional[str]:
        local_pg = (
            REPO_ROOT
            / "tools"
            / "pgsql"
            / "bin"
            / ("pg_ctl.exe" if IS_WINDOWS else "pg_ctl")
        )
        if local_pg.is_file():
            return str(local_pg)
        system_pg = shutil.which("pg_ctl")
        if system_pg:
            return system_pg
        return None

    def _init_services(self) -> None:
        # 1. PostgreSQL (Port 5432)
        pg_start_cmd: list[str] = []
        if self.postgres_cmd:
            pg_start_cmd = [
                self.postgres_cmd,
                "-D",
                str(DATA_DIR),
                "-l",
                str(LOGS_DIR / "postgres.log"),
                "-w",
                "start",
            ]
        else:
            pg_start_cmd = ["echo", "PostgreSQL service running"]

        self.services["postgres"] = ServiceProcess(
            name="postgres",
            display_name="PostgreSQL 18",
            port=5432,
            start_cmd=pg_start_cmd,
        )

        # 2. FastAPI Backend (Port 8000)
        fastapi_cmd = self.python_cmd + [
            "uvicorn",
            "server.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ]
        backend_env = {
            "PYTHONUNBUFFERED": "1",
            "DATABASE_URL": os.environ.get(
                "DATABASE_URL",
                "postgresql://vitalcer@127.0.0.1:5432/vitalcer",
            ),
        }
        self.services["backend"] = ServiceProcess(
            name="backend",
            display_name="FastAPI Backend",
            port=8000,
            start_cmd=fastapi_cmd,
            env=backend_env,
        )

        # 3. Caddy Reverse Proxy & Static SPA Server (Ports 5173, 5174)
        caddy_cmd = [self.caddy_cmd, "run", "--config", "Caddyfile"]
        self.services["caddy"] = ServiceProcess(
            name="caddy",
            display_name="Caddy Web Server",
            port=5173,
            start_cmd=caddy_cmd,
        )

    def get_service(self, name: str) -> Optional[ServiceProcess]:
        return self.services.get(name)

    def start_service(self, name: str) -> bool:
        srv = self.services.get(name)
        if not srv:
            return False
        started = srv.start()
        if started and name == "postgres" and self.postgres_cmd:
            createdb_bin = (
                Path(self.postgres_cmd).parent
                / ("createdb.exe" if IS_WINDOWS else "createdb")
            )
            if createdb_bin.is_file():
                try:
                    subprocess.run(
                        [
                            str(createdb_bin),
                            "-U",
                            "vitalcer",
                            "-h",
                            "127.0.0.1",
                            "vitalcer",
                        ],
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass
        return started

    def stop_service(self, name: str) -> bool:
        srv = self.services.get(name)
        if not srv:
            return False
        if name == "postgres" and self.postgres_cmd and srv.is_running():
            try:
                subprocess.run(
                    [self.postgres_cmd, "-D", str(DATA_DIR), "-m", "fast", "stop"],
                    check=False,
                )
            except Exception:
                pass
        return srv.stop()

    def start_all(self) -> dict[str, bool]:
        """Start all services in sequence: Postgres -> Backend -> Caddy."""
        results: dict[str, bool] = {}
        results["postgres"] = self.start_service("postgres")
        time.sleep(0.5)
        results["backend"] = self.start_service("backend")
        time.sleep(0.5)
        results["caddy"] = self.start_service("caddy")
        return results

    def stop_all(self) -> dict[str, bool]:
        """Stop all services in reverse order: Caddy -> Backend -> Postgres."""
        results: dict[str, bool] = {}
        results["caddy"] = self.stop_service("caddy")
        results["backend"] = self.stop_service("backend")
        results["postgres"] = self.stop_service("postgres")
        return results

    @staticmethod
    def get_local_ip() -> str:
        """Find the host machine's primary LAN Wi-Fi / Ethernet IP."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"


if __name__ == "__main__":
    manager = ServiceManager()
    local_ip = manager.get_local_ip()
    print("==================================================")
    print(" Vitalcer Store Server Manager CLI")
    print(f" Local Wi-Fi IP: {local_ip}")
    print(f" Mobile POS Camera Link: https://{local_ip}:5174")
    print(" Admin Dashboard:        http://localhost:5173")
    print("==================================================")

    if "--check" in sys.argv:
        for name, srv in manager.services.items():
            status = "RUNNING ✅" if srv.is_running() else "STOPPED ⏹️"
            print(f"  • {srv.display_name} (Port {srv.port}): {status}")
        sys.exit(0)

    if "--start-all" in sys.argv:
        print("Starting all services...")
        manager.start_all()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down all services cleanly...")
            manager.stop_all()
            print("Done.")
