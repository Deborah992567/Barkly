import Foundation

struct APIHistoryRepository: HistoryRepository {
    private let client: APIClient
    private let pageSize: Int

    init(client: APIClient, pageSize: Int = 20) {
        self.client = client
        self.pageSize = pageSize
    }

    func fetchAllAnalyses() async throws -> [BehaviorAnalysis] {
        var items: [BehaviorAnalysis] = []
        var page = 1
        while true {
            let batch = try await fetchPage(page: page)
            items.append(contentsOf: batch.items)
            guard batch.hasNext else { break }
            page += 1
        }
        return items
    }

    func fetchAnalyses(for dogID: UUID) async throws -> [BehaviorAnalysis] {
        try await fetchAllAnalyses().filter { $0.dogID == dogID }
    }

    func record(_ analysis: BehaviorAnalysis) async throws {
        // Analyses are persisted server-side during the create flow; nothing to do.
    }

    func fetchHistoryPage(
        dogID: UUID? = nil,
        behavior: BehaviorState? = nil,
        page: Int = 1,
        pageSize: Int? = nil
    ) async throws -> HistoryPage {
        var query: [URLQueryItem] = [URLQueryItem(name: "page", value: "\(page)")]
        query.append(URLQueryItem(name: "page_size", value: "\(pageSize ?? self.pageSize)"))
        if let dogID {
            query.append(URLQueryItem(name: "dog_id", value: dogID.uuidString))
        }
        if let behavior {
            query.append(URLQueryItem(name: "behavior", value: behavior.apiValue))
        }
        do {
            let dto: HistoryPageDTO = try await client.get("api/v1/history", query: query)
            return HistoryPage(dto: dto)
        } catch let error as APIClientError {
            throw Self.map(error)
        }
    }

    private func fetchPage(page: Int) async throws -> HistoryPage {
        try await fetchHistoryPage(page: page)
    }

    private static func map(_ error: APIClientError) -> Error {
        switch error {
        case .unauthorized:
            return AppRepositoryError.unauthorized
        case .http(let status, _, _):
            return status == 401 ? AppRepositoryError.unauthorized : AppRepositoryError.serviceUnavailable
        case .transport:
            return AppRepositoryError.offline
        case .decoding, .invalidRequest:
            return AppRepositoryError.invalidData
        }
    }
}