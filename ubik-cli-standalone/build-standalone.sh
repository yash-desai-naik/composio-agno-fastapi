#!/bin/bash
set -e

echo "Building ubik-py standalone binary..."

# Clean up previous builds
rm -rf build dist build-venv *.spec

# Create virtual environment for building
python -m venv build-venv
source build-venv/bin/activate

# Install build dependencies
pip install --upgrade pip wheel setuptools
pip install pyinstaller

# Install runtime dependencies
pip install -r requirements.txt

# Create PyInstaller spec file
cat > ubik-py.spec << EOL
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pkg_resources',
        'agno',
        'composio_agno',
        'pydantic',
        'openai',
        'mcp',
        'python_dotenv',
        'dotenv',
        'typing_extensions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ubik-py',
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
    icon=None,
)
EOL

# Build the binary
pyinstaller ubik-py.spec

echo "Build complete! Standalone binary is in dist/ubik-py"
echo "To install system-wide, run: sudo cp dist/ubik-py /usr/local/bin/"
