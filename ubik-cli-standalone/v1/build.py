#!/usr/bin/env python3
"""
Build script to create a standalone Ubik AI executable
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd: str, cwd: str = None) -> bool:
    """Run a command and return success status"""
    print(f"🔧 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                               capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        print(f"❌ Error output: {e.stderr}")
        return False


def install_pyinstaller():
    """Install PyInstaller for building executables"""
    print("📦 Installing PyInstaller...")
    return run_command("pip install pyinstaller")


def build_executable():
    """Build the standalone executable"""
    print("🏗️  Building standalone executable...")
    
    # PyInstaller command for creating a single executable file
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--name=ubik",                  # Executable name
        "--add-data=ubik_tools.py:.",   # Include ubik_tools.py
        "--hidden-import=agno.models.openai",
        "--hidden-import=composio_agno",
        "--hidden-import=agno.tools.mcp", 
        "--hidden-import=agno.team.team",
        "--hidden-import=agno.agent",
        "--collect-all=agno",
        "--collect-all=composio_agno",
        "--collect-all=openai",
        "--collect-all=mcp",
        "--collect-all=pydantic",
        "--clean",                      # Clean build cache
        "--noconfirm",                  # Overwrite without asking
        "ubik.py"
    ]
    
    return run_command(" ".join(cmd))


def optimize_build():
    """Optimize the build by excluding unnecessary modules"""
    print("⚡ Optimizing build size...")
    
    # Create a more optimized build
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=ubik",
        "--exclude-module=matplotlib",
        "--exclude-module=numpy", 
        "--exclude-module=pandas",
        "--exclude-module=scipy",
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "--exclude-module=jupyter",
        "--exclude-module=notebook",
        "--exclude-module=IPython",
        "--exclude-module=tkinter",
        "--exclude-module=PIL",
        "--hidden-import=agno.models.openai",
        "--hidden-import=composio_agno",
        "--hidden-import=agno.tools.mcp",
        "--hidden-import=agno.team.team", 
        "--hidden-import=agno.agent",
        "--collect-submodules=agno",
        "--collect-submodules=composio_agno",
        "--clean",
        "--noconfirm",
        "ubik.py"
    ]
    
    return run_command(" ".join(cmd))


def create_spec_file():
    """Create a custom .spec file for more control"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ubik.py'],
    pathex=[],
    binaries=[],
    datas=[('ubik_tools.py', '.')],
    hiddenimports=[
        'agno.models.openai',
        'composio_agno', 
        'agno.tools.mcp',
        'agno.team.team',
        'agno.agent',
        'openai',
        'mcp',
        'pydantic',
        'python_dotenv'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 
        'torch', 'tensorflow', 'jupyter', 'notebook',
        'IPython', 'tkinter', 'PIL', 'cv2'
    ],
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
    name='ubik',
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
'''
    
    with open('ubik.spec', 'w') as f:
        f.write(spec_content)
    
    print("📄 Created custom ubik.spec file")
    return True


def build_from_spec():
    """Build using the custom spec file"""
    print("🔨 Building from spec file...")
    return run_command("pyinstaller ubik.spec")


def check_dependencies():
    """Check if all dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import agno
        import composio_agno
        import openai
        import mcp
        import pydantic
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False


def main():
    """Main build function"""
    print("🚀 Ubik AI Standalone Build Script")
    print("=" * 50)
    
    # Check if we have the required files
    if not os.path.exists('ubik.py'):
        print("❌ ubik.py not found!")
        sys.exit(1)
    
    if not os.path.exists('ubik_tools.py'):
        print("❌ ubik_tools.py not found!")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Please install dependencies first")
        sys.exit(1)
    
    # Install PyInstaller
    if not install_pyinstaller():
        print("❌ Failed to install PyInstaller")
        sys.exit(1)
    
    # Method 1: Try optimized build first
    print("\n🎯 Attempting optimized build...")
    if optimize_build():
        print("✅ Optimized build successful!")
    else:
        print("⚠️  Optimized build failed, trying spec file method...")
        
        # Method 2: Use custom spec file
        if create_spec_file() and build_from_spec():
            print("✅ Spec file build successful!")
        else:
            print("⚠️  Spec file build failed, trying basic build...")
            
            # Method 3: Basic build
            if build_executable():
                print("✅ Basic build successful!")
            else:
                print("❌ All build methods failed")
                sys.exit(1)
    
    # Check if executable was created
    dist_path = Path("dist")
    if sys.platform.startswith('win'):
        exe_path = dist_path / "ubik.exe"
    else:
        exe_path = dist_path / "ubik"
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Executable created: {exe_path}")
        print(f"📦 File size: {file_size:.1f} MB")
        
        # Test the executable
        print("\n🧪 Testing executable...")
        test_cmd = f'"{exe_path}" --list_apps --composio_api_key=test'
        if run_command(test_cmd):
            print("✅ Executable test passed!")
        else:
            print("⚠️  Executable test failed (but this might be due to invalid API key)")
        
        print(f"\n🎉 Build complete! Your standalone Ubik AI is at: {exe_path}")
        print("\n📖 Usage:")
        print(f'   {exe_path} --query="what\'s the weather?" --entity_id=you@email.com --openai_key=sk-xxx --composio_api_key=xxx')
        
    else:
        print("❌ Executable not found after build")
        sys.exit(1)


if __name__ == "__main__":
    main()