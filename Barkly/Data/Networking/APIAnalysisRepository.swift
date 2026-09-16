import Foundation

/// Uploads local media to the backend, then creates the analysis referencing the
/// opaque media ids returned by the upload step.
struct APIAnalysisRepository: AnalysisRepository {
    private let client: APIClient

    init(client: APIClient) {
        self.client = client
    }

    func requestAnalysis(
        for dogID: UUID,
        inputType: AnalysisInputType,
        vocalizationType: VocalizationType?,
        duration: TimeInterval?
    ) async throws -> BehaviorAnalysis {
        try await requestAnalysis(
            for: dogID,
            inputType: inputType,
            mediaURLs: [],
            duration: duration,
            context: nil
        )
    }

    func requestAnalysis(
        for dogID: UUID,
        inputType: AnalysisInputType,
        mediaURLs: [URL],
        duration: TimeInterval?,
        context: AnalysisContextInput?
    ) async throws -> BehaviorAnalysis {
        var mediaIDs: [UUID] = []
        do {
            for url in mediaURLs {
                let data = try Data(contentsOf: url)
                let uploadResponse: MediaUploadResponseDTO = try await uploadMedia(
                    data: data,
                    url: url,
                    duration: duration
                )
                mediaIDs.append(uploadResponse.mediaId)
            }
            let body = AnalysisCreateRequestDTO(
                dogId: dogID,
                inputType: inputType.apiValue,
                mediaIds: mediaIDs,
                soundCategory: Self.soundCategory(for: inputType),
                durationMs: apiDurationMillis(duration),
                context: apiContext(context),
                idempotencyKey: Self.idempotencyKey()
            )
            let analysis: AnalysisDTO = try await client.post("api/v1/analyses", body: body)
            return BehaviorAnalysis(dto: analysis)
        } catch let error as APIClientError {
            throw Self.map(error)
        }
    }

    func requestBehaviorAnalysis(
        for dogID: UUID,
        context: AnalysisContextInput?
    ) async throws -> BehaviorAnalysis {
        do {
            let body = AnalysisCreateRequestDTO(
                dogId: dogID,
                inputType: "BEHAVIOR",
                mediaIds: [],
                soundCategory: nil,
                durationMs: nil,
                context: apiContext(context),
                idempotencyKey: Self.idempotencyKey()
            )
            let analysis: AnalysisDTO = try await client.post("api/v1/analyses", body: body)
            return BehaviorAnalysis(dto: analysis)
        } catch let error as APIClientError {
            throw Self.map(error)
        }
    }

    private func uploadMedia(data: Data, url: URL, duration: TimeInterval?) async throws -> MediaUploadResponseDTO {
        let mediaType = Self.mediaType(for: url)
        var form: [(String, String)] = [("media_type", mediaType)]
        if let duration, duration > 0 {
            form.append(("duration_ms", apiDurationMillis(duration).map(String.init) ?? ""))
        }
        let responseData = try await client.upload(
            "api/v1/media/upload",
            fileData: data,
            filename: url.lastPathComponent,
            mimeType: Self.mimeType(for: url),
            form: form
        )
        do {
            return try JSONDecoder.uploadDecoder.decode(MediaUploadResponseDTO.self, from: responseData)
        } catch {
            throw APIClientError.decoding(String(describing: error))
        }
    }

    // MARK: Mapping

    private static func soundCategory(for inputType: AnalysisInputType) -> String? {
        guard inputType == .audio else { return nil }
        return "BARK"
    }

    private static func mediaType(for url: URL) -> String {
        switch url.pathExtension.lowercased() {
        case "mp4", "mov", "m4v": "VIDEO"
        case "jpg", "jpeg", "png", "heic": "IMAGE"
        default: "AUDIO"
        }
    }

    private static func mimeType(for url: URL) -> String {
        switch url.pathExtension.lowercased() {
        case "mp4": "video/mp4"
        case "mov": "video/quicktime"
        case "m4v": "video/x-m4v"
        case "jpg", "jpeg": "image/jpeg"
        case "png": "image/png"
        case "heic": "image/heic"
        case "wav": "audio/wav"
        case "m4a": "audio/m4a"
        default: "application/octet-stream"
        }
    }

    private static func idempotencyKey() -> String {
        let stamp = Int(Date().timeIntervalSince1970 * 1000)
        return "ios-\(stamp)-\(UUID().uuidString.prefix(12))"
    }

    private static func map(_ error: APIClientError) -> Error {
        switch error {
        case .unauthorized:
            return AppRepositoryError.unauthorized
        case .http(let status, _, _):
            switch status {
            case 401: return AppRepositoryError.unauthorized
            case 422: return AppRepositoryError.invalidData
            default: return AppRepositoryError.serviceUnavailable
            }
        case .transport:
            return AppRepositoryError.offline
        case .decoding, .invalidRequest:
            return AppRepositoryError.invalidData
        }
    }
}

private extension JSONDecoder {
    static let uploadDecoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()
}