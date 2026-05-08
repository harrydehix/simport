import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
import tempfile
import re
from pathlib import Path

def get_appdata_dir():
    home = Path.home()
    if sys.platform == "win32":
        return Path(os.environ.get('APPDATA', home / 'AppData' / 'Roaming')) / 'vibes'
    elif sys.platform == "darwin":
        return home / 'Library' / 'Application Support' / 'vibes'
    else:
        return home / '.local' / 'share' / 'vibes'

def is_command_available(cmd):
    return shutil.which(cmd) is not None

def run_cmd(cmd, cwd=None, shell=False, check=True, quiet=False):
    if not quiet:
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        print(f"Running: {cmd_str}")
    return subprocess.run(cmd, cwd=cwd, shell=shell, check=check, text=True, capture_output=True)

def check_valid_ffmpeg(user_data_path=None):
    try:
        ffmpeg_cmd = "ffmpeg"
        if sys.platform == "win32":
            base = Path(user_data_path) if user_data_path else get_appdata_dir()
            ffmpeg_exe = base / "ffmpeg" / "bin" / "ffmpeg.exe"
            if ffmpeg_exe.exists():
                ffmpeg_cmd = str(ffmpeg_exe)
        elif sys.platform == "darwin":
            base = Path(user_data_path) if user_data_path else get_appdata_dir()
            ffmpeg_exe = base / "ffmpeg" / "bin" / "ffmpeg"
            if ffmpeg_exe.exists():
                ffmpeg_cmd = str(ffmpeg_exe)

        res = run_cmd([ffmpeg_cmd, "-version"], quiet=True)
        stdout = res.stdout

        match = re.search(r"ffmpeg version [a-zA-Z]*(\d+\.\d+(\.\d+)?)", stdout)
        current_version = match.group(1) if match else "unknown"

        if not current_version.startswith("7."):
            return False, current_version, f"requires v7.x, but found v{current_version}"

        if sys.platform == "win32" and "--enable-shared" not in stdout:
            return False, current_version, f"found v{current_version}, but it is not a shared build (--enable-shared missing)"

        return True, current_version, ""
    except Exception as e:
        return False, "unknown", "Command not found or execution failed"

def ensure_ffmpeg(user_data_path=None):
    valid, version, reason = check_valid_ffmpeg(user_data_path)
    if valid:
        print(f"✅ ffmpeg (v{version}) is already installed and valid.")
        return

    print(f"🔄 ffmpeg validation failed ({reason}). Attempting to install proper v7...")
    base_app_data = Path(user_data_path) if user_data_path else get_appdata_dir()
    
    try:
        if sys.platform == "win32":
            ffmpeg_base_dir = base_app_data / "ffmpeg"
            temp_zip = Path(tempfile.gettempdir()) / "ffmpeg.zip"
            
            print(f"Downloading Portable FFmpeg (v7.1.1 Shared) to {temp_zip}...")
            urllib.request.urlretrieve('https://github.com/GyanD/codexffmpeg/releases/download/7.1.1/ffmpeg-7.1.1-full_build-shared.zip', temp_zip)
            
            print(f"Extracting FFmpeg to {ffmpeg_base_dir}...")
            temp_extract = base_app_data / "ffmpeg_temp"
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_extract)
            
            if ffmpeg_base_dir.exists():
                shutil.rmtree(ffmpeg_base_dir)
            
            extracted_folder = temp_extract / "ffmpeg-7.1.1-full_build-shared"
            extracted_folder.rename(ffmpeg_base_dir)
            shutil.rmtree(temp_extract)
            temp_zip.unlink()
            print(f"✅ portable ffmpeg installed to {ffmpeg_base_dir}")
            
        elif sys.platform == "darwin":
            ffmpeg_base_dir = base_app_data / "ffmpeg"
            temp_zip = Path(tempfile.gettempdir()) / "ffmpeg-mac.zip"
            
            print(f"Downloading static ffmpeg (v7.1.1) for macOS to {temp_zip}...")
            run_cmd(["curl", "-L", "https://evermeet.cx/ffmpeg/ffmpeg-7.1.1.zip", "-o", str(temp_zip)])
            
            print(f"Extracting ffmpeg to {ffmpeg_base_dir}/bin...")
            bin_dir = ffmpeg_base_dir / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            run_cmd(["unzip", "-o", str(temp_zip), "-d", str(bin_dir)])
            temp_zip.unlink()
            print(f"✅ portable ffmpeg installed to {ffmpeg_base_dir}")
            
        elif sys.platform.startswith("linux"):
            print("⚠️ On Linux, trying to install ffmpeg via apt-get which might require root privileges.")
            run_cmd("sudo apt-get update && sudo apt-get install -y ffmpeg", shell=True)
        else:
            raise Exception(f"Unsupported OS for automatic ffmpeg installation: {sys.platform}")
        
        print("✅ ffmpeg installed successfully.")
    except Exception as e:
        raise Exception(f"❌ Failed to install ffmpeg automatically. Error: {e}")

def ensure_uv():
    if is_command_available("uv"):
        print("✅ uv is already installed.")
        return

    print("🔄 uv not found. Attempting to install...")
    try:
        if sys.platform == "win32":
            run_cmd(["powershell", "-ExecutionPolicy", "ByPass", "-c", "irm https://astral.sh/uv/install.ps1 | iex"])
            os.environ["PATH"] = f"{Path.home() / '.cargo' / 'bin'};{os.environ.get('PATH', '')}"
        else:
            run_cmd("curl -LsSf https://astral.sh/uv/install.sh | sh", shell=True)
            os.environ["PATH"] = f"{Path.home() / '.local' / 'bin'}:{os.environ.get('PATH', '')}"
        
        print("✅ uv installed successfully.")
    except Exception as e:
        raise Exception(f"❌ Failed to install uv automatically. Error: {e}")

def has_cuda():
    try:
        run_cmd(["nvidia-smi"], quiet=True)
        return True
    except Exception:
        return False

def ensure_pytorch(project_root):
    print("🔄 Checking PyTorch requirements...")
    install_cmd = ['uv', 'pip', 'install', 'torch~=2.6.0', 'torchvision~=0.21.0', 'torchaudio~=2.6.0']
    
    if sys.platform == "darwin":
        print("🍎 Detected macOS. Using default PyTorch build (MPS supported natively).")
    else:
        cuda_available = has_cuda()
        if cuda_available:
            print("🟩 Detected NVIDIA GPU. Installing PyTorch with CUDA 12.6 support...")
            install_cmd.extend(["--index-url", "https://download.pytorch.org/whl/cu126"])
        else:
            print("⬜ No NVIDIA GPU detected. Installing PyTorch with CPU support...")
            if sys.platform.startswith("linux"):
                install_cmd.extend(["--index-url", "https://download.pytorch.org/whl/cpu"])

    try:
        run_cmd(["uv", "sync"], cwd=project_root)
        print("✅ UV dependencies installed successfully.")
        install_cmd.append("--reinstall")
        run_cmd(install_cmd, cwd=project_root)
        print("✅ PyTorch installed successfully.")
    except Exception as e:
        raise Exception(f"❌ Failed to install PyTorch automatically. Error: {e}")

def ensure_simport_installed(project_root=None, force_reinstall=False, vibes_integration=False):
    if not project_root:
        project_root = get_appdata_dir() / "vibes" / "simport" if vibes_integration else Path(__file__).parent
    else:
        project_root = Path(project_root)
    
    print(f"🚀 Starting simport installation process in {project_root.resolve()}...")
    
    try:
        # 0. Download source if missing
        if not (project_root / "pyproject.toml").exists():
            print(f"🔄 Downloading simport source to {project_root}...")
            zip_url = "https://github.com/harrydehix/vibes-ai-based-import/archive/refs/heads/main.zip"
            temp_zip = Path(tempfile.gettempdir()) / "simport-src.zip"
            
            urllib.request.urlretrieve(zip_url, temp_zip)
            
            temp_extract = Path(tempfile.gettempdir()) / "simport_extract"
            if temp_extract.exists():
                shutil.rmtree(temp_extract)
            
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_extract)
                
            project_root.mkdir(parents=True, exist_ok=True)
            
            src_folder = temp_extract / "vibes-ai-based-import-main"
            for item in src_folder.iterdir():
                shutil.move(str(item), str(project_root / item.name))
                
            shutil.rmtree(temp_extract)
            temp_zip.unlink()
            print("✅ simport source downloaded and extracted.")

        # 1. Ensure prerequisites
        ensure_ffmpeg(project_root.parent)
        ensure_uv()

        # 2. Check if simport is already installed via uv
        if is_command_available("simport") and not force_reinstall:
            print("✅ simport CLI is already installed.")
            ensure_pytorch(project_root)
            return

        print("🔄 Installing simport via uv tool...")

        # 3. Install tool using uv in editable mode
        install_cmd = ["uv", "tool", "install", "--python", "3.12", "--editable", "."]
        
        if sys.platform == "win32" and has_cuda():
            install_cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/cu126", "--index-strategy", "unsafe-best-match"])
        elif sys.platform.startswith("linux") and not has_cuda():
            install_cmd.extend(["--extra-index-url", "https://download.pytorch.org/whl/cpu", "--index-strategy", "unsafe-best-match"])
            
        if force_reinstall:
            install_cmd.append("--reinstall")
            
        res = subprocess.run(install_cmd, cwd=project_root, text=True, capture_output=True)
        if res.returncode != 0:
            print(f"⚠️ uv tool install failed or output warnings: {res.stderr}")
        
        # Ensure PyTorch correctly falls back to hardware versions
        ensure_pytorch(project_root)
        
        print("✅ simport installed successfully. You can now use the simport CLI!")
        
    except Exception as e:
        print(f"❌ Error during simport installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Install simport")
    parser.add_argument("--project-root", default=None, help="Root directory the project is installed into")
    parser.add_argument("--force-reinstall", default=False, action="store_true", help="Force reinstall of simport via UV")
    parser.add_argument("--vibes-integration", default=False, action="store_true", help="Enable vibes integration")
    
    args = parser.parse_args()
    
    ensure_simport_installed(args.project_root, args.force_reinstall, args.vibes_integration)