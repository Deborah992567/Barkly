import XCTest
@testable import Barkly

@MainActor
final class AnalysisFlowControllerTests: XCTestCase {

    private func makeContainer(
        permissionMode: MockPermissionService.Mode = .granted
    ) -> AppContainer {
        let permissions = MockPermissionService(mode: permissionMode)
        let dogRepository = MockDogRepository()
        let historyRepository = MockHistoryRepository(latency: 0)
        return AppContainer(dependencies: AppDependencies(
            dogRepository: dogRepository,
            analysisRepository: MockAnalysisRepository(latency: 0),
            historyRepository: historyRepository,
            insightsRepository: MockInsightsRepository(history: historyRepository),
            permissionService: permissions,
            owner: MockSeeds.owner,
            initialDogs: MockSeeds.demoDogs
        ))
    }

    func testRecordRouteRequestsPermissionAndEntersRecording() async {
        let container = makeContainer()
        let controller = AnalysisFlowController(container: container)
        await controller.begin(route: .record)
        XCTAssertEqual(controller.inputType, .audio)
        XCTAssertTrue(controller.recordingStarts)
    }

    func testDeniedMicrophoneFailsWithSettingsRecovery() async {
        let container = makeContainer(permissionMode: .denied)
        let controller = AnalysisFlowController(container: container)
        await controller.begin(route: .record)
        guard case .failed = controller.phase else {
            return XCTFail("expected a failed phase for denied permission")
        }
    }

    func testVideoRouteStaysIdleUntilSubmission() async {
        let container = makeContainer()
        let controller = AnalysisFlowController(container: container)
        await controller.begin(route: .video)
        XCTAssertEqual(controller.inputType, .video)
        XCTAssertEqual(controller.phase, .idle)
    }

    func testSubmissionMovesToProcessingThenReady() async {
        let container = makeContainer()
        let controller = AnalysisFlowController(container: container)
        await controller.begin(route: .record)
        await controller.submitRecording(duration: 3)
        XCTAssertEqual(controller.result?.estimatedState, .attentionSeeking)
        XCTAssertEqual(Float(controller.result?.confidence ?? -1), 0.82, accuracy: 0.0001)
    }

    func testSubmissionRecordsToHistory() async {
        let container = makeContainer()
        let controller = AnalysisFlowController(container: container)
        await controller.begin(route: .record)
        await controller.submitRecording(duration: 2)
        let stored = try? await container.historyRepository.fetchAnalyses(for: MockSeeds.max.id)
        let relevant = stored?.filter { $0.estimatedState == .attentionSeeking }.count ?? 0
        XCTAssertEqual(relevant, MockSeeds.demoAnalyses().filter { $0.dogID == MockSeeds.max.id && $0.estimatedState == .attentionSeeking }.count + 1)
    }

    func testSubmissionWithNoDogFails() async {
        let dogRepository = MockDogRepository()
        let historyRepository = MockHistoryRepository(latency: 0)
        let container = AppContainer(dependencies: AppDependencies(
            dogRepository: dogRepository,
            analysisRepository: MockAnalysisRepository(latency: 0),
            historyRepository: historyRepository,
            insightsRepository: MockInsightsRepository(history: historyRepository),
            permissionService: MockPermissionService(mode: .granted),
            owner: MockSeeds.owner,
            initialDogs: []
        ))
        let controller = AnalysisFlowController(container: container)
        await controller.begin(route: .record)
        await controller.submitRecording(duration: 3)
        guard case .failed(let error) = controller.phase else {
            return XCTFail("expected failure")
        }
        XCTAssertEqual(error.title, "No dog selected")
    }

    func testResetToSelectionReturnsToIdle() async {
        let container = makeContainer()
        let controller = AnalysisFlowController(container: container)
        await controller.begin(route: .video)
        XCTAssertEqual(controller.phase, .idle)
        controller.resetToSelection()
        XCTAssertEqual(controller.phase, .idle)
    }
}