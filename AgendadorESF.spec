# -*- mode: python ; coding: utf-8 -*-
# Build em modo PASTA (onedir): o exe abre instantaneamente porque não precisa
# se extrair inteiro para %TEMP% a cada inicialização (o onefile era a principal
# causa da lentidão ao abrir). A pasta dist/AgendadorESF é embutida no instalador.
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    exclude_binaries=True,
    name='AgendadorESF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX desativado: causa falso positivo em antivírus e atrasa a abertura
    # (o Windows re-verifica o exe compactado a cada execução).
    upx=False,
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
    upx_exclude=[],
    name='AgendadorESF',
)
