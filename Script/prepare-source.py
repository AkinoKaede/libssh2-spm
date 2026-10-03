#!/usr/bin/env python3
"""Export official libssh2 and apply patches only in an ignored build directory."""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile


def prepare(root, output):
    output = output.resolve()
    build = (root / ".build").resolve()
    if output == build or not output.is_relative_to(build):
        raise ValueError("Patched source must be a subdirectory of .build")
    upstream = root / "Vendor/libssh2"
    if not (upstream / ".git").exists():
        raise ValueError("Run git submodule update --init --recursive first")
    with tempfile.TemporaryDirectory(prefix="libssh2-patch-") as temporary:
        staging = Path(temporary)
        archive = staging / "source.tar"
        subprocess.run(["git", "-C", str(upstream), "archive", "--format=tar",
                        f"--output={archive}", "HEAD"], check=True)
        source = staging / "source"
        source.mkdir()
        subprocess.run(["tar", "-xf", str(archive), "-C", str(source)], check=True)
        subprocess.run(["bash", str(root / "Script/apply-patches.sh"), str(source)], check=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(source, output, symlinks=True)
    print(f"Prepared disposable patched source: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".build/patched-native"))
    args = parser.parse_args()
    try:
        prepare(Path(__file__).resolve().parent.parent, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Source preparation failed: {error}\n")
