"""Vitalcer Desktop Control Panel (XAMPP-Style GUI).

Native Windows desktop status dashboard and process control interface built with
Python's standard library tkinter. Manages PostgreSQL, FastAPI, and Caddy services
with real-time status lights, quick launch buttons, LAN IP display, and live logs.
"""

from __future__ import annotations

import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

# Add repository root to path
if getattr(sys, "frozen", False):
    REPO_ROOT = Path(sys.executable).resolve().parent
else:
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.windows.service_manager import ServiceManager  # noqa: E402


class VitalcerControlApp:
    """XAMPP-style GUI Control Panel for Vitalcer single-store stack."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Vitalcer Store Server — Panel de Control")
        self.root.geometry("820x640")
        self.root.minsize(760, 560)

        self.manager = ServiceManager()
        self.local_ip = self.manager.get_local_ip()

        # Connect log stream callback
        for srv in self.manager.services.values():
            srv.add_log_listener(self._on_service_log)

        self._setup_styles()
        self._build_ui()

        # Window closing handler for clean shutdown
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Periodic status refresh
        self._poll_status()

    def _setup_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Configure colors
        style.configure(
            "Header.TLabel",
            font=("Segoe UI", 16, "bold"),
            foreground="#0f172a",
        )
        style.configure(
            "Subheader.TLabel",
            font=("Segoe UI", 9),
            foreground="#64748b",
        )
        style.configure(
            "Card.TFrame",
            background="#f8fafc",
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=5,
        )

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding="14")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header Banner
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_lbl = ttk.Label(
            header_frame,
            text="🌿 Vitalcer Store Server",
            style="Header.TLabel",
        )
        title_lbl.pack(anchor=tk.W)

        sub_lbl = ttk.Label(
            header_frame,
            text="Panel de Control • PostgreSQL 18 • FastAPI • Caddy Web Server",
            style="Subheader.TLabel",
        )
        sub_lbl.pack(anchor=tk.W)

        # 2. Local Network IP Banner (Phone POS Access)
        net_card = tk.LabelFrame(
            main_frame,
            text=" 📱 Acceso Móvil (Red Local Wi-Fi) ",
            font=("Segoe UI", 9, "bold"),
            bg="#f0fdf4",
            fg="#166534",
            padx=12,
            pady=8,
        )
        net_card.pack(fill=tk.X, pady=(0, 12))

        pos_url = f"https://{self.local_ip}:5174"
        admin_url = "http://localhost:5173"

        net_text = (
            f"• Lector de Cámara POS (Celulares en Wi-Fi):  {pos_url}\n"
            f"• Admin & Catálogo (PC de Mostrador):       {admin_url}"
        )
        net_lbl = tk.Label(
            net_card,
            text=net_text,
            font=("Consolas", 10, "bold"),
            bg="#f0fdf4",
            fg="#15803d",
            justify=tk.LEFT,
        )
        net_lbl.pack(side=tk.LEFT, padx=4)

        btn_copy = tk.Button(
            net_card,
            text="Copiar Link POS",
            font=("Segoe UI", 8, "bold"),
            bg="#dcfce7",
            fg="#166534",
            activebackground="#bbf7d0",
            relief="groove",
            command=lambda: self._copy_to_clipboard(pos_url),
            cursor="hand2",
        )
        btn_copy.pack(side=tk.RIGHT, padx=4)

        # 3. Services Grid (XAMPP-Style)
        srv_frame = tk.LabelFrame(
            main_frame,
            text=" Estado de Servicios ",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
        )
        srv_frame.pack(fill=tk.X, pady=(0, 12))

        # Grid headers
        tk.Label(
            srv_frame,
            text="Servicio",
            font=("Segoe UI", 9, "bold"),
            width=18,
            anchor="w",
        ).grid(row=0, column=0, padx=4, pady=3)
        tk.Label(
            srv_frame,
            text="Puerto",
            font=("Segoe UI", 9, "bold"),
            width=10,
            anchor="center",
        ).grid(row=0, column=1, padx=4, pady=3)
        tk.Label(
            srv_frame,
            text="Estado",
            font=("Segoe UI", 9, "bold"),
            width=16,
            anchor="center",
        ).grid(row=0, column=2, padx=4, pady=3)
        tk.Label(
            srv_frame,
            text="Acciones",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).grid(row=0, column=3, padx=4, pady=3)

        self.service_rows: dict[str, dict[str, tk.Widget]] = {}

        services_info = [
            (
                "postgres",
                "PostgreSQL 18",
                "5432",
                [("Logs DB", lambda: self._view_db_logs())],
            ),
            (
                "backend",
                "FastAPI Backend",
                "8000",
                [("API Docs", lambda: webbrowser.open("http://localhost:8000/docs"))],
            ),
            (
                "caddy",
                "Caddy Web Server",
                "5173 / 5174",
                [
                    ("Abrir Admin", lambda: webbrowser.open("http://localhost:5173")),
                    ("Abrir POS", lambda: webbrowser.open("https://localhost:5174")),
                ],
            ),
        ]

        for idx, (srv_key, name, port_str, extra_btns) in enumerate(
            services_info, start=1
        ):
            tk.Label(srv_frame, text=name, font=("Segoe UI", 9), anchor="w").grid(
                row=idx, column=0, padx=4, pady=4, sticky="w"
            )
            tk.Label(
                srv_frame,
                text=port_str,
                font=("Segoe UI", 9, "bold"),
                fg="#475569",
                anchor="center",
            ).grid(row=idx, column=1, padx=4, pady=4)

            # Status pill
            status_lbl = tk.Label(
                srv_frame,
                text="VERIFICANDO...",
                font=("Segoe UI", 8, "bold"),
                bg="#f1f5f9",
                fg="#64748b",
                padx=8,
                pady=2,
                relief="groove",
                width=14,
            )
            status_lbl.grid(row=idx, column=2, padx=4, pady=4)

            # Button container
            actions_subframe = tk.Frame(srv_frame)
            actions_subframe.grid(row=idx, column=3, padx=4, pady=4, sticky="w")

            btn_toggle = tk.Button(
                actions_subframe,
                text="Iniciar",
                font=("Segoe UI", 8, "bold"),
                bg="#e2e8f0",
                width=8,
                command=lambda k=srv_key: self._toggle_service(k),
                cursor="hand2",
            )
            btn_toggle.pack(side=tk.LEFT, padx=2)

            for btn_text, btn_cmd in extra_btns:
                extra_b = tk.Button(
                    actions_subframe,
                    text=btn_text,
                    font=("Segoe UI", 8),
                    bg="#f8fafc",
                    command=btn_cmd,
                    cursor="hand2",
                )
                extra_b.pack(side=tk.LEFT, padx=2)

            self.service_rows[srv_key] = {
                "status_lbl": status_lbl,
                "toggle_btn": btn_toggle,
            }

        # 4. Global Action Bar
        global_bar = ttk.Frame(main_frame)
        global_bar.pack(fill=tk.X, pady=(0, 10))

        btn_start_all = tk.Button(
            global_bar,
            text="▶️ Iniciar Todo",
            font=("Segoe UI", 9, "bold"),
            bg="#22c55e",
            fg="white",
            activebackground="#16a34a",
            padx=10,
            pady=4,
            command=self._start_all_async,
            cursor="hand2",
        )
        btn_start_all.pack(side=tk.LEFT, padx=(0, 6))

        btn_stop_all = tk.Button(
            global_bar,
            text="⏹️ Detener Todo",
            font=("Segoe UI", 9, "bold"),
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            padx=10,
            pady=4,
            command=self._stop_all_async,
            cursor="hand2",
        )
        btn_stop_all.pack(side=tk.LEFT, padx=6)

        btn_open_pos = tk.Button(
            global_bar,
            text="📱 Abrir POS (Caja)",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="white",
            activebackground="#0369a1",
            padx=10,
            pady=4,
            command=lambda: webbrowser.open("https://localhost:5174"),
            cursor="hand2",
        )
        btn_open_pos.pack(side=tk.RIGHT, padx=(6, 0))

        btn_open_admin = tk.Button(
            global_bar,
            text="📊 Abrir Admin",
            font=("Segoe UI", 9, "bold"),
            bg="#475569",
            fg="white",
            activebackground="#334155",
            padx=10,
            pady=4,
            command=lambda: webbrowser.open("http://localhost:5173"),
            cursor="hand2",
        )
        btn_open_admin.pack(side=tk.RIGHT, padx=6)

        # 5. Live Console Log Viewer
        log_frame = tk.LabelFrame(
            main_frame,
            text=" Registro de Ejecución (Consola en Vivo) ",
            font=("Segoe UI", 9, "bold"),
            padx=4,
            pady=4,
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = ScrolledText(
            log_frame,
            font=("Consolas", 9),
            bg="#0f172a",
            fg="#f8fafc",
            insertbackground="white",
            wrap=tk.WORD,
            height=8,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        log_actions = ttk.Frame(log_frame)
        log_actions.pack(fill=tk.X, pady=(4, 0))

        btn_clear = tk.Button(
            log_actions,
            text="Limpiar Registro",
            font=("Segoe UI", 8),
            command=self._clear_logs,
        )
        btn_clear.pack(side=tk.RIGHT)

    def _copy_to_clipboard(self, text: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copiado", f"Enlace copiado al portapapeles:\n{text}")

    def _view_db_logs(self) -> None:
        log_file = REPO_ROOT / "data" / "logs" / "postgres.log"
        if log_file.is_file():
            try:
                webbrowser.open(str(log_file))
            except Exception:
                pass
        else:
            messagebox.showinfo(
                "Logs DB", "No se encontró archivo de log de PostgreSQL aún."
            )

    def _on_service_log(self, message: str) -> None:
        def append() -> None:
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)

        self.root.after(0, append)

    def _clear_logs(self) -> None:
        self.log_text.delete("1.0", tk.END)

    def _toggle_service(self, srv_key: str) -> None:
        srv = self.manager.get_service(srv_key)
        if not srv:
            return

        def task() -> None:
            if srv.is_running():
                self.manager.stop_service(srv_key)
            else:
                self.manager.start_service(srv_key)
            self.root.after(100, self._update_service_status)

        threading.Thread(target=task, daemon=True).start()

    def _start_all_async(self) -> None:
        def task() -> None:
            self.manager.start_all()
            self.root.after(100, self._update_service_status)

        threading.Thread(target=task, daemon=True).start()

    def _stop_all_async(self) -> None:
        def task() -> None:
            self.manager.stop_all()
            self.root.after(100, self._update_service_status)

        threading.Thread(target=task, daemon=True).start()

    def _update_service_status(self) -> None:
        for srv_key, row in self.service_rows.items():
            srv = self.manager.get_service(srv_key)
            status_lbl = row["status_lbl"]
            toggle_btn = row["toggle_btn"]

            if not srv:
                continue

            if srv.is_running():
                status_lbl["text"] = "🟢 EN EJECUCIÓN"
                status_lbl["bg"] = "#dcfce7"
                status_lbl["fg"] = "#15803d"
                toggle_btn["text"] = "Detener"
                toggle_btn["bg"] = "#fee2e2"
                toggle_btn["fg"] = "#b91c1c"
            else:
                status_lbl["text"] = "🔴 DETENIDO"
                status_lbl["bg"] = "#f1f5f9"
                status_lbl["fg"] = "#64748b"
                toggle_btn["text"] = "Iniciar"
                toggle_btn["bg"] = "#e2e8f0"
                toggle_btn["fg"] = "#0f172a"

    def _poll_status(self) -> None:
        self._update_service_status()
        self.root.after(2000, self._poll_status)

    def _on_close(self) -> None:
        running = any(s.is_running() for s in self.manager.services.values())
        if running:
            msg = (
                "¿Deseas detener todos los servicios antes de salir?\n\n"
                "(Recomendado para liberar los puertos 5432, 8000 y 5174)"
            )
            ans = messagebox.askyesno("Cerrar Servidor Vitalcer", msg)
            if ans:
                self.manager.stop_all()
        self.root.destroy()


def main() -> None:
    if "--backend" in sys.argv or "--server" in sys.argv:
        import uvicorn

        from server.main import app

        uvicorn.run(app, host="0.0.0.0", port=8000)
        return

    root = tk.Tk()
    _app = VitalcerControlApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
