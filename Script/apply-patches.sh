#!/bin/bash
set -euo pipefail
export LC_ALL=C

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <source_dir> [patch_dir]" >&2
    exit 1
fi
SOURCE_DIR=$(cd "$1" && pwd)
PATCH_DIR=$(cd "${2:-$ROOT_DIR/Patches/libssh2}" && pwd)

for patch_file in "$PATCH_DIR"/*; do
    [ -e "$patch_file" ] || continue
    case "$patch_file" in
        *.md) continue ;;
        *.patch)
            if git -C "$SOURCE_DIR" apply --check --reverse "$patch_file" 2>/dev/null; then
                echo "Already applied: $(basename "$patch_file")"
            elif git -C "$SOURCE_DIR" apply --check "$patch_file"; then
                git -C "$SOURCE_DIR" apply "$patch_file"
                echo "Applied: $(basename "$patch_file")"
            else
                echo "Patch conflicts with source: $patch_file" >&2
                exit 1
            fi
            ;;
        *)
            echo "Unsupported patch file: $patch_file" >&2
            exit 1
            ;;
    esac
done
