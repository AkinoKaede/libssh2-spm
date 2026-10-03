import CSSH2
import XCTest

class MyTest: XCTestCase {
    func testExample() {
        XCTAssert(libssh2_init(0) == 0)
        libssh2_exit()
    }

    func testCompleteSignatureAPIIsAvailableAndRejectsInvalidSession() {
        XCTAssertEqual(
            libssh2_userauth_publickey_signed(nil, nil, nil, 0, nil, nil),
            Int32(LIBSSH2_ERROR_BAD_USE)
        )
    }
}
