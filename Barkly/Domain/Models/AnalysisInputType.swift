import Foundation

enum AnalysisInputType: String, Codable, CaseIterable, Sendable {
    case audio
    case video
    case photo
    case behavior

    var title: String {
        switch self {
        case .audio: "Sound recording"
        case .video: "Video"
        case .photo: "Photo"
        case .behavior: "Behavior notes"
        }
    }

    var shortTitle: String {
        switch self {
        case .audio: "Recording"
        case .video: "Video"
        case .photo: "Photo"
        case .behavior: "Observation"
        }
    }

    var symbolName: String {
        switch self {
        case .audio: "waveform"
        case .video: "video.fill"
        case .photo: "photo.fill"
        case .behavior: "eye.fill"
        }
    }

    /// Backend `AnalysisInputType` wire value.
    var apiValue: String {
        switch self {
        case .audio: "AUDIO"
        case .video: "VIDEO"
        case .photo: "IMAGE"
        case .behavior: "BEHAVIOR"
        }
    }

    /// Reverse mapping from the backend's wire value.
    init?(apiValue raw: String) {
        switch raw {
        case "AUDIO": self = .audio
        case "VIDEO": self = .video
        case "IMAGE": self = .photo
        case "BEHAVIOR": self = .behavior
        default: return nil
        }
    }
}