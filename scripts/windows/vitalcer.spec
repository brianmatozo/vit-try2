# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for Vitalcer Control Panel & Backend.

Compiles vitalcer_control.py (Tkinter GUI supervisor + dual-mode FastAPI backend)
into an optimized --onedir distribution for Inno Setup packaging.
"""

import sys
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
    ["scripts/windows/vitalcer_control.py"],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff", "ty", "basedpyright"],
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
    name="vitalcer_control",
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
    name="vitalcer_control",
)
