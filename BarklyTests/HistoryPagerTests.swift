import XCTest
@testable import Barkly

@MainActor
final class HistoryPagerTests: XCTestCase {

    func testInitialPageLoadsAndReportsMore() async {
        let repository = FakeHistoryRepository(pages: [page(ids: [1, 2], hasNext: true)])
        let pager = HistoryPager(repository: repository, pageSize: 2)

        await pager.loadInitial()

        XCTAssertEqual(pager.phase, .loaded(hasNext: true))
        XCTAssertEqual(pager.items.map(\.seed), [2, 1])
    }

    func testEmptyHistoryShowsEmptyPhase() async {
        let repository = FakeHistoryRepository(pages: [page(ids: [], hasNext: false)])
        let pager = HistoryPager(repository: repository, pageSize: 20)

        await pager.loadInitial()

        XCTAssertEqual(pager.phase, .empty)
        XCTAssertTrue(pager.items.isEmpty)
    }

    func testLoadNextPageAppendsAndEnds() async {
        let repository = FakeHistoryRepository(pages: [
            page(ids: [1, 2], hasNext: true),
            page(ids: [3], hasNext: false)
        ])
        let pager = HistoryPager(repository: repository, pageSize: 2)

        await pager.loadInitial()
        await pager.loadNextPage()

        XCTAssertEqual(pager.items.map(\.seed), [3, 2, 1])
        XCTAssertEqual(pager.phase, .loaded(hasNext: false))
    }

    func testLoadNextPageIsIgnoredWhenEndReached() async {
        let repository = FakeHistoryRepository(pages: [page(ids: [1], hasNext: false)])
        let pager = HistoryPager(repository: repository, pageSize: 2)

        await pager.loadInitial()
        await pager.loadNextPage()

        let requested = await repository.requestedPages
        XCTAssertEqual(requested, [1])
    }

    func testRefreshReplacesListWithFirstPage() async {
        let repository = FakeHistoryRepository(pages: [
            page(ids: [1, 2], hasNext: true),
            page(ids: [3], hasNext: false)
        ])
        let pager = HistoryPager(repository: repository, pageSize: 2)

        await pager.loadInitial()
        await pager.loadNextPage()
        await repository.setPage(page(ids: [9, 8], hasNext: true), at: 0)
        await pager.refresh()

        XCTAssertEqual(pager.items.map(\.seed), [9, 8])
        XCTAssertEqual(pager.phase, .loaded(hasNext: true))
    }

    func testOfflineFailureSurfacesOfflinePhase() async {
        let repository = FakeHistoryRepository(pages: [])
        await repository.setError(.offline)
        let pager = HistoryPager(repository: repository, pageSize: 20)

        await pager.loadInitial()

        if case .offline = pager.phase {} else {
            XCTFail("Expected offline phase, got \(pager.phase)")
        }
        XCTAssertTrue(pager.items.isEmpty)
    }

    func testFailureSurfacesFailedPhase() async {
        let repository = FakeHistoryRepository(pages: [])
        await repository.setError(.serviceUnavailable)
        let pager = HistoryPager(repository: repository, pageSize: 20)

        await pager.loadInitial()

        if case .failed = pager.phase {} else {
            XCTFail("Expected failed phase, got \(pager.phase)")
        }
    }

    func testFailedNextPageKeepsItemsAndRetrySucceeds() async {
        let repository = FakeHistoryRepository(pages: [
            page(ids: [1, 2], hasNext: true),
            page(ids: [3], hasNext: false)
        ])
        let pager = HistoryPager(repository: repository, pageSize: 2)

        await pager.loadInitial()
        await repository.setError(.offline)
        await pager.loadNextPage()

        XCTAssertEqual(pager.items.map(\.seed), [2, 1], "Loaded items must survive a failed page request")
        XCTAssertNotNil(pager.moreFailure)
        XCTAssertEqual(pager.phase, .loaded(hasNext: true))

        await repository.setError(nil)
        await pager.retryNextPage()

        XCTAssertNil(pager.moreFailure)
        XCTAssertEqual(pager.items.map(\.seed), [3, 2, 1])
    }

    func testDuplicateIDsAreMergedOnce() async {
        let repository = FakeHistoryRepository(pages: [
            page(ids: [1, 2], hasNext: true),
            page(ids: [2, 3], hasNext: false)
        ])
        let pager = HistoryPager(repository: repository, pageSize: 2)

        await pager.loadInitial()
        await pager.loadNextPage()

        XCTAssertEqual(pager.items.map(\.seed), [3, 2, 1])
    }

    private func page(ids: [Int], hasNext: Bool) -> HistoryPage {
        HistoryPage(
            items: ids.map { seed in
                BehaviorAnalysis(
                    id: UUID(uuidString: String(format: "00000000-0000-0000-0000-%012d", seed))!,
                    dogID: MockSeeds.max.id,
                    createdAt: Date(timeIntervalSince1970: TimeInterval(seed)),
                    inputType: .audio,
                    estimatedState: .calm,
                    confidence: 0.7,
                    observations: ["Observation"],
                    explanation: "Explanation"
                )
            },
            page: 1,
            pageSize: ids.count,
            total: ids.count + (hasNext ? 1 : 0),
            hasNext: hasNext
        )
    }
}

private extension BehaviorAnalysis {
    var seed: Int {
        Int(id.uuidString.suffix(12)) ?? 0
    }
}

private actor FakeHistoryRepository: HistoryRepository {
    private var pages: [HistoryPage]
    private(set) var requestedPages: [Int] = []
    private var error: AppRepositoryError?

    init(pages: [HistoryPage]) {
        self.pages = pages
    }

    func setError(_ error: AppRepositoryError?) {
        self.error = error
    }

    func setPage(_ page: HistoryPage, at index: Int) {
        guard pages.indices.contains(index) else { return }
        pages[index] = page
    }

    func fetchHistoryPage(
        dogID: UUID?,
        behavior: BehaviorState?,
        page: Int,
        pageSize: Int?
    ) async throws -> HistoryPage {
        requestedPages.append(page)
        if let error { throw error }
        let index = page - 1
        guard pages.indices.contains(index) else {
            return HistoryPage(
                items: [],
                page: page,
                pageSize: pageSize ?? 20,
                total: 0,
                hasNext: false
            )
        }
        return pages[index]
    }

    func fetchAllAnalyses() async throws -> [BehaviorAnalysis] {
        throw AppRepositoryError.serviceUnavailable
    }

    func fetchAnalyses(for dogID: UUID) async throws -> [BehaviorAnalysis] {
        throw AppRepositoryError.serviceUnavailable
    }

    func record(_ analysis: BehaviorAnalysis) async throws {}
}