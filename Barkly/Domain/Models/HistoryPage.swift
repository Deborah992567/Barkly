import Foundation

/// A page of analyses returned by the backend's paginated history endpoint.
struct HistoryPage: Equatable, Sendable {
    let items: [BehaviorAnalysis]
    let page: Int
    let pageSize: Int
    let total: Int
    let hasNext: Bool

    var isEmpty: Bool {
        items.isEmpty
    }
}