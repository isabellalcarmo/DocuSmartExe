# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_all,
)

# Dados de diretórios próprios
datas = [
    ('modelos', 'modelos'),
    ('tesseract', 'tesseract'),
    ('poppler-24.08.0', 'poppler-24.08.0')
]

# Dados das bibliotecas
datas += collect_data_files('transformers')
datas += collect_data_files('sentence_transformers')
datas += collect_data_files('certifi')

# Coleta completa de módulos com metadados e arquivos .typed
pydantic_all = collect_all('pydantic')
httpx_all = collect_all('httpx')
supabase_all = collect_all('supabase')

datas += pydantic_all[1]
datas += httpx_all[1]
datas += supabase_all[1]

hiddenimports = []
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('sentence_transformers')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('pydantic_core')
hiddenimports += collect_submodules('httpx')
hiddenimports += collect_submodules('httpcore')
hiddenimports += collect_submodules('anyio')
hiddenimports += collect_submodules('sniffio')
hiddenimports += collect_submodules('supabase')
hiddenimports += collect_submodules('gotrue')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('torch.cuda')
hiddenimports += collect_submodules('asyncio')

# Inclui os hiddenimports extras coletados com collect_all
hiddenimports += pydantic_all[2]
hiddenimports += httpx_all[2]
hiddenimports += supabase_all[2]

# Imports manuais adicionais para cobertura total
hiddenimports += [
    'pydantic_core._pydantic_core',
    'pydantic.v1',
    'asyncio',
    'asyncio.base_events',
    'asyncio.events',
    'asyncio.windows_events',
    'asyncio.windows_utils',
    'asyncio.selector_events',
    'asyncio.proactor_events',
    'asyncio.coroutines',
    'asyncio.tasks',
    'asyncio.futures',
    'typing_extensions',
    'json',
    'datetime',
    'ctypes',
    'ssl',
    'concurrent',
    'concurrent.futures',
    'win32ctypes.core',
    'queue',
    'selectors',
    'pkg_resources.extern',
    'pkg_resources.py2_warn'
]

# Remover duplicatas
final_hiddenimports = list(set(hiddenimports))

# Caminho base do projeto
pathex = [os.path.abspath('.')]

a = Analysis(
    ['docusmart_app.py'],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=final_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['fix_asyncio.py'],  # Certifique-se de criar esse arquivo
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
    name='DocuSmartApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # ATIVADO para ver traceback no terminal durante testes
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="C:/Users/isabe/Downloads/robot-head.ico"
)
