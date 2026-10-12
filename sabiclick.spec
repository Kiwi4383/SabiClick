# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('/nix/store/cqkkaqcv84vp0nj7dk7c5zi406lpjmdh-tcl-8.6.16/lib/tcl8.6', '_tcl_data'), ('/nix/store/61499qa4jm46j1i3y533xi0vla0dx8kz-tk-8.6.16/lib/tk8.6', '_tk_data'), ('LICENSE', '.'), ('NOTICE', '.')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='sabiclick',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
