import Foundation
import Observation

/// Drives the paginated History screen. All data comes from the live
/// `HistoryRepository`; there is no mock fallback when a request fails.
@MainActor
@Observable
final class HistoryPager {
    enum Phase: Equatable {
        case loading
        case loaded(hasNext: Bool)
        case empty
        case failed(AppFailure)
        case offline(AppFailure)
    }

    private let repository: any HistoryRepository
    private let pageSize: Int

    private(set) var items: [BehaviorAnalysis] = []
    private(set) var phase: Phase = .loading
    private(set) var isLoadingMore = false
    private(set) var moreFailure: AppFailure?

    private var nextPage = 1
    private var generation = 0

    init(repository: any HistoryRepository, pageSize: Int = 20) {
        self.repository = repository
        self.pageSize = pageSize
    }

    /// Loads (or reloads) the first page. Replaces everything currently shown.
    func loadInitial() async {
        generation += 1
        let token = generation
        items = []
        moreFailure = nil
        phase = .loading

        do {
            let page = try await repository.fetchHistoryPage(
                dogID: nil,
                behavior: nil,
                page: 1,
                pageSize: pageSize
            )
            guard token == generation else { return }
            items = Self.merge([], page.items)
            nextPage = page.page + 1
            if items.isEmpty {
                phase = .empty
            } else {
                phase = .loaded(hasNext: page.hasNext)
            }
        } catch {
            guard token == generation else { return }
            let failure = ErrorMapper.failure(for: error)
            phase = ErrorMapper.isOffline(error) ? .offline(failure) : .failed(failure)
        }
    }

    /// Pull-to-refresh: fetches the current first page and replaces the list.
    func refresh() async {
        await loadInitial()
    }

    /// Appends the next page. Safe to call repeatedly; SwiftUI lifecycle
    /// duplicates are ignored while a request is in flight.
    func loadNextPage() async {
        guard case .loaded(let hasNext) = phase, hasNext, !isLoadingMore else { return }
        isLoadingMore = true
        moreFailure = nil
        let token = generation
        defer { isLoadingMore = false }

        do {
            let page = try await repository.fetchHistoryPage(
                dogID: nil,
                behavior: nil,
                page: nextPage,
                pageSize: pageSize
            )
            guard token == generation else { return }
            items = Self.merge(items, page.items)
            nextPage = page.page + 1
            phase = .loaded(hasNext: page.hasNext)
        } catch {
            guard token == generation else { return }
            moreFailure = ErrorMapper.failure(for: error)
        }
    }

    /// Retries the failed next-page request without discarding loaded items.
    func retryNextPage() async {
        await loadNextPage()
    }

    /// De-duplicates by analysis id and keeps the newest first, so life-cycle
    /// repeats never create duplicate rows.
    private static func merge(_ existing: [BehaviorAnalysis], _ incoming: [BehaviorAnalysis]) -> [BehaviorAnalysis] {
        var seen = Set(existing.map(\.id))
        var merged = existing
        for analysis in incoming where !seen.contains(analysis.id) {
            seen.insert(analysis.id)
            merged.append(analysis)
        }
        return merged.sorted { $0.createdAt > $1.createdAt }
    }
}