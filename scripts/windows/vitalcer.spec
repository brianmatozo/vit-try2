# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for Vitalcer Headless Launcher & Backend Server.

Compiles launcher.py into an optimized headless --onedir distribution (vitalcer.exe)
for Inno Setup packaging. Zero console windows or Tkinter dependencies.
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

REPO_ROOT = Path.cwd()

hiddenimports = [
    # Uvicorn internals
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "asyncio",
    # FastAPI & Pydantic
    "fastapi",
    "starlette",
    "starlette.middleware",
    "starlette.middleware.cors",
    "pydantic",
    "pydantic_core",
    # SQLModel & Database Drivers
    "sqlmodel",
    "sqlalchemy",
    "sqlalchemy.dialects.postgresql",
    "sqlalchemy.dialects.postgresql.psycopg",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.aiosqlite",
    "psycopg",
    "psycopg_binary",
    "aiosqlite",
    # App modules
] + collect_submodules("server") + collect_submodules("scripts.windows")

a = Analysis(
    ["scripts/windows/launcher.py"],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "ruff",
        "ty",
        "basedpyright",
        "tkinter",
        "_tkinter",
        "tcl",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="vitalcer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="vitalcer",
)
