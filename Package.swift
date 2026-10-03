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
        .binaryTarget(name: "CSSH2Native", path: "BinaryTarget/CSSH2Native.xcframework"),
        .testTarget(name: "CSSH2Test", dependencies: ["CSSH2"]),
    ]
)
