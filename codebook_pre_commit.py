"""Run a verified official Codebook binary from the pre-commit environment."""

import hashlib
import io
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen
import zipfile

VERSION = "0.3.42"
CHECKSUMS = {
    "aarch64-apple-darwin": "d0a17c11eaccb7d08091c195e5908956be67a05554fc0df9a0842988387a1852",
    "x86_64-apple-darwin": "e826b9890ff2e6c4be9207f427e87a04818dd600bf99d6dbf4c9eab3c39aa331",
    "aarch64-unknown-linux-musl": "5f1448369447f0f61e407e0082cd72a89f2ea7e47e3c45692b910a9b03adb6fe",
    "x86_64-unknown-linux-musl": "979b9a92f7a433c8830b51783dd06aab1d2668aee991c22d42560b593d291f9c",
    "aarch64-pc-windows-msvc": "fa1e47992d5ff72cb24cbb3105f6a796d0ac70a67cd9aa763d8770ad0fd11df5",
    "x86_64-pc-windows-msvc": "a0d0b01ce1e40522590859a66063b884bb6c494c5e45595aaf0eb77c2fd7afe6",
}


def binary():
    machine = platform.machine().lower()
    arch = {"arm64": "aarch64", "amd64": "x86_64"}.get(machine, machine)
    system = platform.system()
    target = f"{arch}-" + {
        "Darwin": "apple-darwin",
        "Linux": "unknown-linux-musl",
        "Windows": "pc-windows-msvc",
    }.get(system, system)
    if target not in CHECKSUMS:
        raise RuntimeError(f"Unsupported Codebook platform: {target}")

    name = "codebook-lsp.exe" if system == "Windows" else "codebook-lsp"
    destination = Path(__file__).parent / f"codebook-{VERSION}-{target}" / name
    if destination.is_file():
        return destination

    extension = "zip" if system == "Windows" else "tar.gz"
    url = (f"https://github.com/blopker/codebook/releases/download/v{VERSION}/"
           f"codebook-lsp-{target}.{extension}")
    with urlopen(url, timeout=120) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != CHECKSUMS[target]:
        raise RuntimeError("Codebook archive SHA-256 verification failed")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        extracted = Path(temporary) / name
        # Copy only the executable; never extract archive-controlled paths.
        if extension == "zip":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                with archive.open(name) as source, extracted.open("wb") as output:
                    shutil.copyfileobj(source, output)
        else:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
                member = archive.getmember(name)
                if not member.isfile():
                    raise RuntimeError("Codebook archive executable is not a regular file")
                with archive.extractfile(member) as source, extracted.open("wb") as output:
                    shutil.copyfileobj(source, output)
        extracted.chmod(0o755)
        extracted.replace(destination)
    return destination


def main():
    try:
        return subprocess.call([str(binary()), "lint", *sys.argv[1:]])
    except (OSError, RuntimeError, ValueError, KeyError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(f"codebook-pre-commit: {error}", file=sys.stderr)
        return 2
