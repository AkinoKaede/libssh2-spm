#!/usr/bin/env python3
"""Verify patch preparation without changing the official source checkout."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class SourceTests(unittest.TestCase):
    def command(self, *command, success=True, cwd=None):
        result = subprocess.run(command, cwd=cwd or self.root, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="libssh2-source-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.upstream = self.root / "Vendor/libssh2"
        self.output = self.root / ".build/patched-native"
        self.upstream.mkdir(parents=True)
        shutil.copytree(Path(__file__).resolve().parent, self.root / "Script")
        (self.root / "Patches/libssh2").mkdir(parents=True)
        self.command("git", "init", "--quiet", str(self.upstream))
        (self.upstream / "auth.c").write_text("legacy signature\n")
        self.command("git", "add", ".", cwd=self.upstream)
        self.command("git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "upstream", cwd=self.upstream)
        (self.upstream / "auth.c").write_text("complete signature\n")
        self.patch = self.root / "Patches/libssh2/0001-signature.patch"
        self.patch.write_text(self.command("git", "diff", cwd=self.upstream).stdout)
        self.command("git", "restore", "auth.c", cwd=self.upstream)

    def prepare(self, *args, success=True):
        return self.command("python3", str(self.root / "Script/prepare-source.py"), *args, success=success)

    def test_applies_patch_only_to_disposable_export(self):
        self.prepare()
        self.assertEqual((self.output / "auth.c").read_text(), "complete signature\n")
        self.assertEqual(self.command("git", "status", "--porcelain", cwd=self.upstream).stdout, "")
        self.command("bash", str(self.root / "Script/apply-patches.sh"), str(self.output))
        self.assertEqual((self.output / "auth.c").read_text(), "complete signature\n")

    def test_conflict_preserves_previous_export(self):
        self.prepare()
        self.patch.write_text(self.patch.read_text().replace("-legacy signature", "-other source"))
        self.prepare(success=False)
        self.assertEqual((self.output / "auth.c").read_text(), "complete signature\n")

    def test_rejects_output_outside_build_and_build_root(self):
        for path in (self.upstream, self.root / ".build"):
            self.prepare("--output", str(path), success=False)
        self.assertEqual(self.command("git", "status", "--porcelain", cwd=self.upstream).stdout, "")

    def test_rejects_unknown_patch_type(self):
        (self.patch.parent / "unexpected.txt").write_text("not a patch")
        self.prepare(success=False)
        self.assertFalse(self.output.exists())

    def test_patch_order_is_lexical(self):
        (self.patch.parent / "0002-next.patch").write_text(
            self.patch.read_text().replace("-legacy signature", "-complete signature")
            .replace("+complete signature", "+next signature"))
        self.prepare()
        self.assertEqual((self.output / "auth.c").read_text(), "next signature\n")


if __name__ == "__main__":
    unittest.main()
