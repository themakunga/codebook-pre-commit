import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import codebook_pre_commit as adapter


class AdapterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        for name, value in (
            ("__file__", str(Path(temporary.name) / "codebook_pre_commit.py")),
            ("CHECKSUMS", adapter.CHECKSUMS.copy()),
        ):
            patcher = patch.object(adapter, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def archive(self, system, name="codebook-lsp", content=b"executable", symlink=False):
        data = io.BytesIO()
        if system == "Windows":
            with zipfile.ZipFile(data, "w") as archive:
                archive.writestr(name + ".exe", content)
        else:
            with tarfile.open(fileobj=data, mode="w:gz") as archive:
                member = tarfile.TarInfo(name)
                member.size = len(content)
                if symlink:
                    member.type = tarfile.SYMTYPE
                    member.linkname = "/outside"
                archive.addfile(member, io.BytesIO(content))
        return data.getvalue()

    def test_download_cache_and_platforms(self):
        for system, machine, target in (
            ("Darwin", "arm64", "aarch64-apple-darwin"),
            ("Linux", "x86_64", "x86_64-unknown-linux-musl"),
            ("Windows", "AMD64", "x86_64-pc-windows-msvc"),
        ):
            with self.subTest(system=system):
                data = self.archive(system)
                adapter.CHECKSUMS[target] = hashlib.sha256(data).hexdigest()
                with patch.object(adapter.platform, "system", return_value=system), \
                     patch.object(adapter.platform, "machine", return_value=machine), \
                     patch.object(adapter, "urlopen", return_value=io.BytesIO(data)) as download:
                    result = adapter.binary()
                    self.assertEqual(result.read_bytes(), b"executable")
                    self.assertEqual(adapter.binary(), result)
                    download.assert_called_once()

    def test_checksum_failure_does_not_cache_binary(self):
        with patch.object(adapter.platform, "system", return_value="Darwin"), \
             patch.object(adapter.platform, "machine", return_value="arm64"), \
             patch.object(adapter, "urlopen", return_value=io.BytesIO(b"tampered")):
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                adapter.binary()
        self.assertFalse(list(Path(adapter.__file__).parent.glob("codebook-*")))

    def test_archive_symlink_is_rejected(self):
        data = self.archive("Darwin", symlink=True)
        adapter.CHECKSUMS["aarch64-apple-darwin"] = hashlib.sha256(data).hexdigest()
        with patch.object(adapter.platform, "system", return_value="Darwin"), \
             patch.object(adapter.platform, "machine", return_value="arm64"), \
             patch.object(adapter, "urlopen", return_value=io.BytesIO(data)):
            with self.assertRaisesRegex(RuntimeError, "regular file"):
                adapter.binary()

    def test_unsupported_platform_does_not_download(self):
        with patch.object(adapter.platform, "system", return_value="Linux"), \
             patch.object(adapter.platform, "machine", return_value="s390x"), \
             patch.object(adapter, "urlopen") as download:
            with self.assertRaisesRegex(RuntimeError, "Unsupported"):
                adapter.binary()
            download.assert_not_called()

    def test_arguments_and_exit_status_are_preserved(self):
        with patch.object(adapter, "binary", return_value=Path("/binary")), \
             patch.object(adapter.sys, "argv", ["adapter", "--suggest", "a file.md"]), \
             patch.object(adapter.subprocess, "call", return_value=1) as run:
            self.assertEqual(adapter.main(), 1)
            run.assert_called_once_with(["/binary", "lint", "--suggest", "a file.md"])

    def test_download_errors_return_failure(self):
        with patch.object(adapter, "binary", side_effect=OSError("offline")), \
             patch.object(adapter.sys, "stderr", io.StringIO()) as errors:
            self.assertEqual(adapter.main(), 2)
            self.assertIn("offline", errors.getvalue())

    def test_allow_failure_only_ignores_spelling_errors(self):
        for status in (0, 1, 2):
            with self.subTest(status=status), \
                 patch.object(adapter, "binary", return_value=Path("/binary")), \
                 patch.object(adapter.sys, "argv", ["adapter", "--allow-failure", "--suggest", "a file.md"]), \
                 patch.object(adapter.sys, "stderr", io.StringIO()) as errors, \
                 patch.object(adapter.subprocess, "call", return_value=status) as run:
                self.assertEqual(adapter.main(), 0 if status == 1 else status)
                run.assert_called_once_with(["/binary", "lint", "--suggest", "a file.md"])
                self.assertEqual("advisory" in errors.getvalue(), status == 1)

    def test_allow_failure_keeps_download_errors_blocking(self):
        with patch.object(adapter, "binary", side_effect=OSError("offline")), \
             patch.object(adapter.sys, "argv", ["adapter", "--allow-failure", "file.md"]), \
             patch.object(adapter.sys, "stderr", io.StringIO()):
            self.assertEqual(adapter.main(), 2)
