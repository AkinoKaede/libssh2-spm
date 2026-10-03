#!/usr/bin/env python3
"""Select a local CI binary or a checksummed release artifact for SwiftPM."""

import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--local", type=Path)
group.add_argument("--url")
parser.add_argument("--archive", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
if args.local:
    target = f'.binaryTarget(name: "CSSH2Native", path: {json.dumps(str(args.local))})'
else:
    if not args.archive or not args.url.startswith("https://"):
        parser.error("Release manifests require an HTTPS URL and --archive")
    checksum = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    target = (f'.binaryTarget(name: "CSSH2Native", url: {json.dumps(args.url)}, '
              f'checksum: "{checksum}")')
(root / "Package.swift").write_text((root / "Package.swift.template").read_text().replace("__BINARY_TARGET__", target))
