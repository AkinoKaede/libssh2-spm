# libssh2-spm

Swift package exposing `CSSH2` on Apple platforms. The native library is built
by GitHub Actions from the official [libssh2](https://github.com/libssh2/libssh2)
submodule plus the numbered patches in `Patches/libssh2`. SwiftPM downloads a
checksummed XCFramework; the public product and external-signature API remain
`CSSH2` and `libssh2_userauth_publickey_signed`.

## Source ownership

`Vendor/libssh2` is a clean official Git submodule. Its gitlink is the native
version pin. Do not commit upstream source snapshots or patched source copies.
CI exports the pinned tree into ignored `.build/patched-native`, applies the
patch stack there, and builds `CSSH2Native.xcframework` for macOS, Mac Catalyst,
iOS, tvOS, watchOS, visionOS, and their simulators. Only the XCFramework archive
is published as a GitHub release asset. The official checkout stays unmodified.

`Source/Exports.swift` is a handwritten one-line module re-export so existing
`import CSSH2` callers keep working with the binary module. It contains no
libssh2 implementation. OpenSSL remains a separate SwiftPM dependency, pinned
to the same version used by CI to compile the native library. zlib is linked
through the wrapper target.

## Maintenance and validation

Change the submodule pin or numbered patches. The update workflow proposes
official stable libssh2 tags and runs the patch regressions. Patch conflicts
fail the build instead of dropping local changes. For local reproduction of CI:

```sh
git submodule update --init --recursive
python3 Script/test-source.py
python3 Script/prepare-source.py
cmake -S .build/patched-native -B .build/native -DCRYPTO_BACKEND=OpenSSL \
  -DBUILD_SHARED_LIBS=OFF -DBUILD_EXAMPLES=OFF \
  -DRUN_DOCKER_TESTS=OFF -DRUN_SSHD_TESTS=OFF
cmake --build .build/native --parallel 2
ctest --test-dir .build/native --output-on-failure

bash Script/download-openssl.sh
python3 Script/build-xcframework.py --openssl .build/openssl/OpenSSL.Package.xcframework
python3 Script/build-manifest.py --local BinaryTarget/CSSH2Native.xcframework
swift test
./Script/test.sh
# The local manifest is temporary; restore it after testing.
git restore Package.swift
```

## Releases

Dispatch **Release XCFramework** on `termind` with an unused package version.
The workflow requires native patch tests, a complete native platform build,
macOS binary consumer tests, and all ten Apple consumer builds. It then
publishes an immutable `binary.<commit>.<run>` artifact, writes its URL and
SHA-256 checksum into `Package.swift`, verifies the remote binary consumer,
and commits and tags the release. Generated C sources are never committed.

Update Termind's maintenance gitlink, exact package version and resolved
revision together after release. `2.0.3-termind-4` is the first CI binary
release. The earlier source-snapshot/overlay history and its tags were corrected;
use the new version to avoid stale caches of rewritten tags. Historical
`2.0.3-termind-1` references the unavailable former nested fork.
