#!/usr/bin/env python3
"""Compile patched libssh2 for Apple platforms; no generated source is committed."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import plistlib
import shutil
import subprocess


def run(*command):
    subprocess.run([str(value) for value in command], check=True)


# Each slice preserves the package's supported deployment targets. arm64
# variants use the first OS release available on that architecture.
PLATFORMS = [
    ("macos", "macosx", "macos", None, {"arm64": "arm64-apple-macos11.0", "x86_64": "x86_64-apple-macos10.13"}),
    ("ios", "iphoneos", "ios", None, {"arm64": "arm64-apple-ios12.0"}),
    ("ios-simulator", "iphonesimulator", "ios", "simulator", {"arm64": "arm64-apple-ios14.0-simulator", "x86_64": "x86_64-apple-ios12.0-simulator"}),
    ("maccatalyst", "macosx", "ios", "maccatalyst", {"arm64": "arm64-apple-ios14.0-macabi", "x86_64": "x86_64-apple-ios13.1-macabi"}),
    ("tvos", "appletvos", "tvos", None, {"arm64": "arm64-apple-tvos12.0"}),
    ("tvos-simulator", "appletvsimulator", "tvos", "simulator", {"arm64": "arm64-apple-tvos14.0-simulator", "x86_64": "x86_64-apple-tvos12.0-simulator"}),
    ("watchos", "watchos", "watchos", None, {"arm64": "arm64-apple-watchos10.0", "arm64_32": "arm64_32-apple-watchos5.0", "armv7k": "armv7k-apple-watchos5.0"}),
    ("watchos-simulator", "watchsimulator", "watchos", "simulator", {"arm64": "arm64-apple-watchos7.0-simulator", "x86_64": "x86_64-apple-watchos5.0-simulator"}),
    ("visionos", "xros", "xros", None, {"arm64": "arm64-apple-xros1.0"}),
    ("visionos-simulator", "xrsimulator", "xros", "simulator", {"arm64": "arm64-apple-xros1.0-simulator"}),
]
DEFINES = """HAVE_LIBSSL LIBSSH2_OPENSSL HAVE_LIBZ LIBSSH2_HAVE_ZLIB STDC_HEADERS
HAVE_STDLIB_H HAVE_STDIO_H HAVE_INTTYPES_H HAVE_UNISTD_H HAVE_ALLOCA HAVE_ALLOCA_H
HAVE_ARPA_INET_H HAVE_NETINET_IN_H HAVE_SYS_SOCKET_H HAVE_SYS_UN_H HAVE_SYS_IOCTL_H
HAVE_SYS_PARAM_H HAVE_SYS_SELECT_H HAVE_SYS_TIME_H HAVE_SYS_UIO_H HAVE_GETTIMEOFDAY
HAVE_SELECT HAVE_SNPRINTF HAVE_STRTOLL HAVE_O_NONBLOCK HAVE_FIONBIO""".split()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openssl", type=Path, required=True)
    parser.add_argument("--platform", choices=[item[0] for item in PLATFORMS])
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    source = root / ".build/patched-native"
    build = root / ".build/xcframework"
    output = root / "BinaryTarget/CSSH2Native.xcframework"
    openssl = args.openssl.resolve()
    libraries = plistlib.loads((openssl / "Info.plist").read_bytes())["AvailableLibraries"]
    run("python3", root / "Script/prepare-source.py", "--output", source)
    headers = build / "Headers"
    if headers.exists():
        shutil.rmtree(headers)
    shutil.copytree(source / "include", headers)
    create = ["xcodebuild", "-create-xcframework"]
    for name, sdk, platform, variant, architectures in PLATFORMS:
        if args.platform and name != args.platform:
            continue
        library = next(item for item in libraries if item["SupportedPlatform"] == platform
                       and item.get("SupportedPlatformVariant") == variant)
        crypto_headers = openssl / library["LibraryIdentifier"] / library["HeadersPath"]
        sysroot = subprocess.check_output(["xcrun", "--sdk", sdk, "--show-sdk-path"], text=True).strip()
        archives = []
        for arch, target in architectures.items():
            assert arch in library["SupportedArchitectures"], (name, arch)
            objects = build / name / arch
            objects.mkdir(parents=True, exist_ok=True)
            sources = sorted((source / "src").glob("*.c"))
            def compile_file(file):
                run("xcrun", "--sdk", sdk, "clang", "-c", file, "-o", objects / (file.stem + ".o"),
                    "-target", target, "-isysroot", sysroot, "-std=c11", "-O2", "-fPIC",
                    "-Wno-deprecated-declarations", "-I", source / "include", "-I", crypto_headers,
                    *[f"-D{value}" for value in DEFINES])
            with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 2, 8)) as executor:
                list(executor.map(compile_file, sources))
            archive = objects / "libCSSH2Native.a"
            run("xcrun", "libtool", "-static", "-o", archive,
                *[objects / (file.stem + ".o") for file in sources])
            archives.append(archive)
        fat = build / name / "libCSSH2Native.a"
        run("xcrun", "lipo", "-create", *archives, "-output", fat)
        framework = build / name / "CSSH2Native.framework"
        if framework.exists():
            shutil.rmtree(framework)
        shutil.copytree(headers, framework / "Headers")
        shutil.copy2(fat, framework / "CSSH2Native")
        (framework / "Modules").mkdir()
        (framework / "Modules/module.modulemap").write_text(
            'framework module CSSH2Native {\n  header "libssh2.h"\n'
            '  header "libssh2_publickey.h"\n  header "libssh2_sftp.h"\n  export *\n}\n'
        )
        (framework / "Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "CSSH2Native",
            "CFBundleIdentifier": "de.akinokae.libssh2.CSSH2Native",
            "CFBundleName": "CSSH2Native", "CFBundlePackageType": "FMWK",
            "CFBundleShortVersionString": "1.0", "CFBundleVersion": "1",
        }))
        create.extend(["-framework", framework])
        print(f"Built {name}: {', '.join(architectures)}", flush=True)
    if output.exists():
        shutil.rmtree(output)
    output.parent.mkdir(exist_ok=True)
    run(*create, "-output", output)
    shutil.copy2(source / "COPYING", output / "LICENSE.libssh2")
    run("ditto", "-c", "-k", "--keepParent", output, root / ".build/CSSH2Native.xcframework.zip")


if __name__ == "__main__":
    main()
