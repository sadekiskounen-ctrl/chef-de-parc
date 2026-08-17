# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/hppor/OneDrive/Desktop/Chef de parc-ayris/GestionParc/main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/hppor/OneDrive/Desktop/Chef de parc-ayris/GestionParc/assets', 'assets')],
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
    name='SARL_NOMADE_Ayris',
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
    icon=['C:/Users/hppor/OneDrive/Desktop/Chef de parc-ayris/GestionParc/assets/ayris.ico'],
)
