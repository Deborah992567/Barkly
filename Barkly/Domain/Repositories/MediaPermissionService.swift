import Foundation
import AVFoundation

enum MediaType: Sendable {
    case microphone
    case camera
}

enum MediaPermissionStatus: Equatable, Sendable {
    case granted
    case denied
    case restricted
    case notDetermined
    case unavailable
}

protocol MediaPermissionServicing: Sendable {
    func status(for mediaType: MediaType) async -> MediaPermissionStatus
    func requestAccess(for mediaType: MediaType) async -> MediaPermissionStatus
}

actor SystemMediaPermissionService: MediaPermissionServicing {
    func status(for mediaType: MediaType) async -> MediaPermissionStatus {
        switch mediaType {
        case .microphone:
            switch AVCaptureDevice.authorizationStatus(for: .audio) {
            case .authorized: .granted
            case .denied: .denied
            case .restricted: .restricted
            case .notDetermined: .notDetermined
            @unknown default: .unavailable
            }
        case .camera:
            switch AVCaptureDevice.authorizationStatus(for: .video) {
            case .authorized: .granted
            case .denied: .denied
            case .restricted: .restricted
            case .notDetermined: .notDetermined
            @unknown default: .unavailable
            }
        }
    }

    func requestAccess(for mediaType: MediaType) async -> MediaPermissionStatus {
        switch mediaType {
        case .microphone:
            let granted = await AVCaptureDevice.requestAccess(for: .audio)
            return granted ? .granted : .denied
        case .camera:
            let granted = await AVCaptureDevice.requestAccess(for: .video)
            return granted ? .granted : .denied
        }
    }
}

actor MockPermissionService: MediaPermissionServicing {
    let mode: Mode

    enum Mode: Sendable {
        case granted
        case denied
        case restricted
    }

    init(mode: Mode = .granted) {
        self.mode = mode
    }

    func status(for mediaType: MediaType) async -> MediaPermissionStatus {
        switch mode {
        case .granted: .granted
        case .denied: .denied
        case .restricted: .restricted
        }
    }

    func requestAccess(for mediaType: MediaType) async -> MediaPermissionStatus {
        await status(for: mediaType)
    }
}