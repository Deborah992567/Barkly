import Foundation

// MARK: - Auth

struct UserDTO: Decodable, Sendable {
    let id: UUID
    let email: String
    let displayName: String?
    let createdAt: Date
}

struct TokenResponseDTO: Decodable, Sendable {
    let accessToken: String
    let tokenType: String
    let expiresIn: Int
    let user: UserDTO
}

// MARK: - Dogs

struct DogDTO: Decodable, Sendable {
    let id: UUID
    let name: String
    let breed: String?
    let sex: String?
    let dateOfBirth: Date?
    let notes: String?
    let createdAt: Date
    let updatedAt: Date
}

struct DogCreateDTO: Encodable, Sendable {
    let name: String
    let breed: String?
    let sex: String?
    let dateOfBirth: Date?
    let notes: String?
}

// MARK: - Media

struct MediaUploadResponseDTO: Decodable, Sendable {
    let mediaId: UUID
    let mediaType: String
    let originalFilename: String?
    let mimeType: String
    let fileSize: Int
    let durationMs: Int?
    let createdAt: Date
}

// MARK: - Analysis

struct ObservationDTO: Decodable, Sendable {
    let category: String
    let description: String
}

struct AnalysisContextDTO: Decodable, Sendable {
    let ownerPresence: String?
    let activityState: String?
    let timeOfDay: String?
    let recentFeeding: Bool?
    let recentWalk: Bool?
    let recentPlay: Bool?
    let presenceOfStrangers: Bool?
    let presenceOfOtherAnimals: Bool?
    let recentStressfulEvent: Bool?
    let locationCategory: String?
    let notes: String?
}

struct AnalysisMediaDTO: Decodable, Sendable {
    let mediaId: UUID
    let mediaType: String
    let originalFilename: String?
    let mimeType: String
    let fileSize: Int?
    let durationMs: Int?
    let createdAt: Date?
}

struct FailureDTO: Decodable, Sendable {
    let code: String
    let message: String
}

struct AnalysisResultDTO: Decodable, Sendable {
    let primaryBehavior: String
    let confidence: Double
    let secondaryBehaviors: [String]
    let detectedAudioCategory: String?
    let observations: [ObservationDTO]
    let explanation: String
    let disclaimer: String
    let provider: String
    let modelName: String
    let modelVersion: String
    let isPlaceholder: Bool
    let generatedAt: Date
    let audioModelName: String?
    let audioModelVersion: String?
    let visionModelName: String?
    let visionModelVersion: String?
    let preprocessingVersion: String?
    let datasetVersion: String?
    let fusionVersion: String?
    let interpretationVersion: String?
    let inferenceLatencyMs: Int?
    let isInsufficientEvidence: Bool?
    let signalsAvailable: [String: String]?
}

struct AnalysisDTO: Decodable, Sendable {
    let analysisId: UUID
    let dogId: UUID
    let status: String
    let inputType: String
    let createdAt: Date
    let startedAt: Date?
    let completedAt: Date?
    let failure: FailureDTO?
    let result: AnalysisResultDTO?
    let media: [AnalysisMediaDTO]
    let context: AnalysisContextDTO?
}

struct HistoryPageDTO: Decodable, Sendable {
    let items: [AnalysisDTO]
    let page: Int
    let pageSize: Int
    let total: Int
    let hasNext: Bool
}

// MARK: - Request bodies

struct AnalysisCreateRequestDTO: Encodable, Sendable {
    let dogId: UUID
    let inputType: String
    let mediaIds: [UUID]
    let soundCategory: String?
    let durationMs: Int?
    let context: AnalysisContextInputDTO?
    let idempotencyKey: String?
}

struct AnalysisContextInputDTO: Encodable, Sendable {
    let ownerPresence: String?
    let activityState: String?
    let timeOfDay: String?
    let recentFeeding: Bool?
    let recentWalk: Bool?
    let recentPlay: Bool?
    let presenceOfStrangers: Bool?
    let presenceOfOtherAnimals: Bool?
    let recentStressfulEvent: Bool?
    let locationCategory: String?
}

// MARK: - Feedback

struct FeedbackCreateDTO: Encodable, Sendable {
    let verdict: String
    let correctedBehavior: String?
    let comment: String?
}

struct FeedbackDTO: Decodable, Sendable {
    let id: UUID
    let analysisId: UUID
    let verdict: String
    let predictedBehavior: String?
    let correctedBehavior: String?
    let comment: String?
    let createdAt: Date
}

// MARK: - Error

struct APIErrorEnvelopeDTO: Decodable, Sendable {
    let code: String?
    let message: String?
    let detail: String?
}