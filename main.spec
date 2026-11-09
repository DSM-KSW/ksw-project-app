# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 빌드 설정: `pyinstaller main.spec` -> dist/dsm-ksw-project/
import os
import urllib.request

import flet_desktop
from PyInstaller.utils.hooks import collect_submodules

# flet_desktop은 실행 시 flet_desktop/app/<archive>가 있으면 그걸 쓰고,
# 없으면 GitHub Releases에서 클라이언트를 내려받는다.
# 빌드할 때 미리 받아서 exe에 같이 넣어 두면 오프라인에서도 바로 실행된다.
flet_version = flet_desktop.version.version
client_archive = flet_desktop.get_artifact_filename()
client_dir = os.path.join(workpath, "flet_client")
client_path = os.path.join(client_dir, client_archive)

if not os.path.exists(client_path):
    os.makedirs(client_dir, exist_ok=True)
    url = f"https://github.com/flet-dev/flet/releases/download/v{flet_version}/{client_archive}"
    print(f"Downloading Flet client: {url}")
    urllib.request.urlretrieve(url, client_path)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[(client_path, "flet_desktop/app"), ("backend/macro_combo.dll", "backend")],
    hiddenimports=collect_submodules("flet") + collect_submodules("flet_desktop") + ["backend.app", "backend.ipc"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="dsm-ksw-project",
    exclude_binaries=True,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
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
    a.datas,
    strip=False,
    upx=False,
    name="dsm-ksw-project",
)
