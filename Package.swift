// swift-tools-version:6.0
import PackageDescription

let package = Package(
    name: "CSSH2",
    platforms: [.iOS(.v12), .macOS(.v10_13), .tvOS(.v12), .watchOS(.v5), .visionOS(.v1)],
    products: [.library(name: "CSSH2", targets: ["CSSH2"])],
    dependencies: [.package(url: "https://github.com/Lakr233/openssl-spm.git", exact: "3.6.2")],
    targets: [
        .target(
            name: "CSSH2",
            dependencies: ["CSSH2Native", .product(name: "OpenSSL", package: "openssl-spm")],
            path: "Source",
            linkerSettings: [.linkedLibrary("z")]
        ),
        .binaryTarget(name: "CSSH2Native", url: "https://github.com/AkinoKaede/libssh2-spm/releases/download/binary.7de8997d60ec.37089190589/CSSH2Native.xcframework.zip", checksum: "2f40606e507a1c3d4be544ede6e723726c07dd9ea049b20b2ff3d71a34188f7a"),
        .testTarget(name: "CSSH2Test", dependencies: ["CSSH2"]),
    ]
)
