# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop.pyw'],
    pathex=[],
    binaries=[],
    datas=[('movie-icon.ico', '.'), ('movie-icon.png', '.'), ('index.html', '.'), ('styles.css', '.'), ('script.js', '.')],
    hiddenimports=['webview', 'fpdf', 'spellchecker', 'editor', 'tkinter', 'tkinter.filedialog'],
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
    name='desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['movie-icon.ico'],
)
