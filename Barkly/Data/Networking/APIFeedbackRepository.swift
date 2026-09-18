import Foundation

enum FeedbackVerdict: String, Sendable {
    case confirmed = "CONFIRMED"
    case incorrect = "INCORRECT"
    case corrected = "CORRECTED"
}

protocol FeedbackRepository: Sendable {
    func submit(
        for analysisID: UUID,
        verdict: FeedbackVerdict,
        correctedBehavior: BehaviorState?,
        comment: String?
    ) async throws
}

struct APIFeedbackRepository: FeedbackRepository {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func submit(
        for analysisID: UUID,
        verdict: FeedbackVerdict,
        correctedBehavior: BehaviorState?,
        comment: String?
    ) async throws {
        let body = FeedbackCreateDTO(
            verdict: verdict.rawValue,
            correctedBehavior: correctedBehavior?.apiValue,
            comment: comment
        )
        do {
            let _: FeedbackDTO = try await client.post(
                "api/v1/analyses/\(analysisID.uuidString)/feedback",
                body: body
            )
        } catch let error as APIClientError {
            throw Self.map(error)
        }
    }

    private static func map(_ error: APIClientError) -> Error {
        AppRepositoryError.from(clientError: error)
    }
}