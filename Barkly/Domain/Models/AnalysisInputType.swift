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
}