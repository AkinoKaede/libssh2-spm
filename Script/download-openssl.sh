#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/openssl
curl --fail --location --retry 3 \
  https://github.com/Lakr233/openssl-spm/releases/download/storage.3.6.2/libssl.xcframework.zip \
  -o .build/openssl/libssl.xcframework.zip
printf '%s  %s\n' \
  329249e8b9ce544aeb698f4adce009d963438ff0ce26a06c7ea152764d362b86 \
  .build/openssl/libssl.xcframework.zip | shasum -a 256 --check
ditto -x -k .build/openssl/libssl.xcframework.zip .build/openssl
