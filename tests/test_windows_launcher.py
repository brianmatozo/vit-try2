"""Unit tests for the Windows headless launcher and service orchestrator."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.windows.launcher import (
    get_app_root,
    is_port_open,
    main,
    start_all,
    start_backend,
    start_caddy,
    start_postgres,
    stop_all,
)


def test_get_app_root() -> None:
    root = get_app_root()
    assert isinstance(root, Path)
    assert (root / "scripts" / "windows").is_dir()


def test_is_port_open_closed_port() -> None:
    # Port 59999 is typically unused
    assert not is_port_open(59999, host="127.0.0.1", timeout=0.05)


@patch("scripts.windows.launcher.is_port_open", return_value=True)
def test_start_postgres_already_running(mock_port: MagicMock) -> None:
    with patch("subprocess.run") as mock_run:
        start_postgres(Path("/dummy"))
        mock_run.assert_not_called()


@patch("scripts.windows.launcher.is_port_open", return_value=False)
def test_start_postgres_triggers_run(mock_port: MagicMock, tmp_path: Path) -> None:
    # Create fake pg_ctl
    bin_dir = tmp_path / "tools" / "pgsql" / "bin"
    bin_dir.mkdir(parents=True)
    fake_pg = bin_dir / "pg_ctl"
    fake_pg.touch()

    with patch("subprocess.run") as mock_run:
        start_postgres(tmp_path)
        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        assert str(fake_pg) in cmd
        assert "start" in cmd


@patch("scripts.windows.launcher.is_port_open", return_value=True)
def test_start_backend_already_running(mock_port: MagicMock) -> None:
    with patch("subprocess.Popen") as mock_popen:
        start_backend(Path("/dummy"))
        mock_popen.assert_not_called()


@patch("scripts.windows.launcher.is_port_open", return_value=False)
def test_start_backend_triggers_popen(mock_port: MagicMock, tmp_path: Path) -> None:
    mock_proc = MagicMock()
    mock_proc.pid = 12345
    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        start_backend(tmp_path)
        assert mock_popen.called
        pid_file = tmp_path / "data" / "logs" / "backend.pid"
        assert pid_file.is_file()
        assert pid_file.read_text(encoding="utf-8") == "12345"


@patch("scripts.windows.launcher.is_port_open", return_value=True)
def test_start_caddy_already_running(mock_port: MagicMock) -> None:
    with patch("subprocess.Popen") as mock_popen:
        start_caddy(Path("/dummy"))
        mock_popen.assert_not_called()


@patch("scripts.windows.launcher.is_port_open", return_value=False)
def test_start_caddy_triggers_popen(mock_port: MagicMock, tmp_path: Path) -> None:
    caddy_dir = tmp_path / "tools" / "caddy"
    caddy_dir.mkdir(parents=True)
    fake_caddy = caddy_dir / "caddy"
    fake_caddy.touch()

    with patch("subprocess.Popen") as mock_popen:
        start_caddy(tmp_path)
        assert mock_popen.called
        cmd = mock_popen.call_args[0][0]
        assert str(fake_caddy) in cmd
        assert "run" in cmd


@patch("scripts.windows.launcher.start_postgres")
@patch("scripts.windows.launcher.start_backend")
@patch("scripts.windows.launcher.start_caddy")
@patch("scripts.windows.launcher.is_port_open", return_value=True)
def test_start_all_calls_subcomponents(
    mock_port: MagicMock,
    mock_caddy: MagicMock,
    mock_backend: MagicMock,
    mock_pg: MagicMock,
) -> None:
    start_all(Path("/dummy"))
    assert mock_pg.called
    assert mock_backend.called
    assert mock_caddy.called


def test_stop_all_cleans_pid_file(tmp_path: Path) -> None:
    pid_dir = tmp_path / "data" / "logs"
    pid_dir.mkdir(parents=True)
    pid_file = pid_dir / "backend.pid"
    pid_file.write_text("999999", encoding="utf-8")

    with patch("subprocess.run"), patch("os.kill"):
        stop_all(tmp_path)
        assert not pid_file.exists()


@patch("scripts.windows.launcher.start_all")
@patch("webbrowser.open")
def test_main_cli_routing(mock_browser: MagicMock, mock_start: MagicMock) -> None:
    # Test --admin
    with patch("sys.argv", ["launcher.py", "--admin"]):
        main()
        assert mock_start.called
        mock_browser.assert_called_with("https://localhost:5173")

    # Test --pos
    with patch("sys.argv", ["launcher.py", "--pos"]):
        main()
        mock_browser.assert_called_with("https://localhost:5174")

    # Test default
    with patch("sys.argv", ["launcher.py"]):
        main()
        mock_browser.assert_called_with("https://localhost:5174")
