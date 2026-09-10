import XCTest
@testable import Barkly

final class ErrorMapperTests: XCTestCase {

    func testOfflineMapsToOfflineFailureWithRetry() {
        let failure = ErrorMapper.failure(for: AppRepositoryError.offline)
        XCTAssertEqual(failure.title, "You're offline")
        XCTAssertEqual(failure.recovery, .retry)
        XCTAssertTrue(ErrorMapper.isOffline(AppRepositoryError.offline))
    }

    func testServiceUnavailableMapsToRetryableFailure() {
        let failure = ErrorMapper.failure(for: AppRepositoryError.serviceUnavailable)
        XCTAssertEqual(failure.title, "Unavailable right now")
        XCTAssertEqual(failure.recovery, .retry)
        XCTAssertFalse(ErrorMapper.isOffline(AppRepositoryError.serviceUnavailable))
    }

    func testInvalidDataMapsToRetryableFailure() {
        let failure = ErrorMapper.failure(for: AppRepositoryError.invalidData)
        XCTAssertEqual(failure.title, "Couldn't read the data")
        XCTAssertEqual(failure.recovery, .retry)
    }

    func testPermissionDeniedMapsToSettingsRecovery() {
        let failure = ErrorMapper.failure(for: AppRepositoryError.permissionDenied)
        XCTAssertEqual(failure.recovery, .openSettings)
    }

    func testUnknownErrorFallsBackToGenericFailure() {
        struct Unknown: Error {}
        let failure = ErrorMapper.failure(for: Unknown())
        XCTAssertEqual(failure.title, "Something went wrong")
        XCTAssertEqual(failure.recovery, .retry)
    }

    func testIsOfflineRecognizesOnlyOffline() {
        XCTAssertFalse(ErrorMapper.isOffline(AppRepositoryError.invalidData))
        XCTAssertFalse(ErrorMapper.isOffline(NSError(domain: "test", code: 1)))
    }
}