import SwiftUI

enum LoadState<Value: Equatable>: Equatable {
    case loading
    case loaded(Value)
    case empty
    case failed(AppFailure)
    case offline(AppFailure)
}

struct AppFailure: Equatable {
    let title: String
    let message: String
    var hint: String? = nil
    var recovery: Recovery? = nil

    enum Recovery: Equatable {
        case retry
        case openSettings
    }
}

enum ErrorMapper {
    static func failure(for error: Error) -> AppFailure {
        if let repositoryError = error as? AppRepositoryError {
            switch repositoryError {
            case .offline:
                return AppFailure(
                    title: "You're offline",
                    message: "BARKLY couldn't reach its service. Your data stays on this device until you reconnect.",
                    hint: "Check your connection and try again.",
                    recovery: .retry
                )
            case .serviceUnavailable:
                return AppFailure(
                    title: "Unavailable right now",
                    message: "BARKLY's service isn't responding. Please try again in a moment.",
                    recovery: .retry
                )
            case .invalidData:
                return AppFailure(
                    title: "Couldn't read the data",
                    message: "This item couldn't be processed. Try again with different media.",
                    recovery: .retry
                )
            case .permissionDenied:
                return AppFailure(
                    title: "Access needed",
                    message: "BARKLY needs access to this media. You can allow it in Settings.",
                    recovery: .openSettings
                )
            }
        }
        return AppFailure(
            title: "Something went wrong",
            message: "The request didn't finish. Please try again.",
            recovery: .retry
        )
    }

    static func isOffline(_ error: Error) -> Bool {
        (error as? AppRepositoryError) == .offline
    }
}

struct LoadableContainer<Value: Equatable, Content: View>: View {
    let state: LoadState<Value>
    var onRetry: (() -> Void)? = nil
    @ViewBuilder let content: (Value) -> Content

    var body: some View {
        switch state {
        case .loading:
            LoadingStateView()
        case .loaded(let value):
            content(value)
        case .empty:
            EmptyStateView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        case .failed(let failure):
            ErrorStateView(failure: failure, onRetry: onRetry)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        case .offline(let failure):
            OfflineStateView(failure: failure, onRetry: onRetry)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}