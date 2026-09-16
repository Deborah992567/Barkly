import Foundation
import Observation
import SwiftUI

enum AppTab: Hashable {
    case home
    case analyze
    case history
    case insights
    case profile
}

enum AnalysisPath: Hashable {
    case record
    case video
    case upload
}

enum AppearanceMode: String, CaseIterable {
    case system
    case light
    case dark

    var displayName: String {
        switch self {
        case .system: "System"
        case .light: "Light"
        case .dark: "Dark"
        }
    }

    var colorScheme: ColorScheme? {
        switch self {
        case .system: nil
        case .light: .light
        case .dark: .dark
        }
    }
}

struct AppDependencies {
    let dogRepository: any DogRepository
    let analysisRepository: any AnalysisRepository
    let historyRepository: any HistoryRepository
    let insightsRepository: any InsightsRepository
    let feedbackRepository: (any FeedbackRepository)?
    let permissionService: any MediaPermissionServicing
    let audioRecorder: any AudioRecording
    let authService: AuthenticationService
    let owner: OwnerProfile
    let initialDogs: [Dog]
    let usesBackend: Bool

    @MainActor
    static var demo: AppDependencies {
        let dogRepository = MockDogRepository()
        let historyRepository = MockHistoryRepository()
        let analysisRepository = MockAnalysisRepository()
        return AppDependencies(
            dogRepository: dogRepository,
            analysisRepository: analysisRepository,
            historyRepository: historyRepository,
            insightsRepository: MockInsightsRepository(history: historyRepository),
            feedbackRepository: nil,
            permissionService: MockPermissionService(mode: .granted),
            audioRecorder: MockAudioRecorder(),
            authService: AuthenticationService(demo: ()),
            owner: MockSeeds.owner,
            initialDogs: MockSeeds.demoDogs,
            usesBackend: false
        )
    }

    @MainActor
    static var live: AppDependencies {
        let session = AuthSessionStore()
        let client = APIClient(config: .development)
        let dogRepository = APIDogRepository(client: client)
        let historyRepository = APIHistoryRepository(client: client)
        return AppDependencies(
            dogRepository: dogRepository,
            analysisRepository: APIAnalysisRepository(client: client),
            historyRepository: historyRepository,
            insightsRepository: DerivedInsightsRepository(history: historyRepository),
            feedbackRepository: APIFeedbackRepository(client: client),
            permissionService: SystemMediaPermissionService(),
            audioRecorder: RealAudioRecorder(),
            authService: AuthenticationService(client: client, session: session),
            owner: OwnerProfile(name: "Barkly Friend", email: "you@example.com"),
            initialDogs: [],
            usesBackend: true
        )
    }
}

@MainActor
@Observable
final class AppContainer {
    let dogRepository: any DogRepository
    let analysisRepository: any AnalysisRepository
    let historyRepository: any HistoryRepository
    let insightsRepository: any InsightsRepository
    let feedbackRepository: (any FeedbackRepository)?
    let permissionService: any MediaPermissionServicing
    let audioRecorder: any AudioRecording
    let authService: AuthenticationService
    let owner: OwnerProfile
    let usesBackend: Bool

    private(set) var dogs: [Dog]
    private(set) var selectedDogID: UUID?
    var hasCompletedOnboarding: Bool
    var pendingAnalysisPath: AnalysisPath? = nil
    var tabSelection: AppTab = .home
    var appearanceMode: AppearanceMode

    private static let onboardingKey = "barkly.hasCompletedOnboarding"
    private static let appearanceKey = "barkly.appearanceMode"

    init(dependencies: AppDependencies) {
        dogRepository = dependencies.dogRepository
        analysisRepository = dependencies.analysisRepository
        historyRepository = dependencies.historyRepository
        insightsRepository = dependencies.insightsRepository
        feedbackRepository = dependencies.feedbackRepository
        permissionService = dependencies.permissionService
        audioRecorder = dependencies.audioRecorder
        authService = dependencies.authService
        owner = dependencies.owner
        usesBackend = dependencies.usesBackend
        dogs = dependencies.initialDogs
        selectedDogID = dependencies.initialDogs.first?.id
        hasCompletedOnboarding = UserDefaults.standard.bool(forKey: Self.onboardingKey)
        appearanceMode = AppearanceMode(rawValue: UserDefaults.standard.string(forKey: Self.appearanceKey) ?? "") ?? .system
    }

    convenience init() {
        self.init(dependencies: .live)
    }

    var selectedDog: Dog? {
        guard let selectedDogID, let dog = dogs.first(where: { $0.id == selectedDogID }) else {
            return dogs.first
        }
        return dog
    }

    func completeOnboarding() {
        hasCompletedOnboarding = true
        UserDefaults.standard.set(true, forKey: Self.onboardingKey)
    }

    func selectDog(id: UUID) {
        selectedDogID = id
    }

    func updateDog(_ dog: Dog) async {
        dogs = dogs.map { $0.id == dog.id ? dog : $0 }
        try? await dogRepository.updateDog(dog)
    }

    /// Refreshes the dog list from the backend after a fresh sign-in.
    func loadDogs() async {
        guard usesBackend else { return }
        do {
            let fetched = try await dogRepository.fetchDogs()
            dogs = fetched
            if selectedDogID == nil || !fetched.contains(where: { $0.id == selectedDogID }) {
                selectedDogID = fetched.first?.id
            }
        } catch {
            // Illegal to crash on connectivity; the UI will surface a retry state.
        }
    }

    func signOut() async {
        dogs = []
        selectedDogID = nil
        await authService.signOut()
    }

    func setAppearanceMode(_ mode: AppearanceMode) {
        appearanceMode = mode
        UserDefaults.standard.set(mode.rawValue, forKey: Self.appearanceKey)
    }

    func openAnalyzer(_ path: AnalysisPath) {
        pendingAnalysisPath = path
        tabSelection = .analyze
    }

    func openTab(_ tab: AppTab) {
        tabSelection = tab
    }
}