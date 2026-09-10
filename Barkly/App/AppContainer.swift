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
    let permissionService: any MediaPermissionServicing
    let owner: OwnerProfile
    let initialDogs: [Dog]

    static var demo: AppDependencies {
        let dogRepository = MockDogRepository()
        let historyRepository = MockHistoryRepository()
        let analysisRepository = MockAnalysisRepository()
        return AppDependencies(
            dogRepository: dogRepository,
            analysisRepository: analysisRepository,
            historyRepository: historyRepository,
            insightsRepository: MockInsightsRepository(history: historyRepository),
            permissionService: MockPermissionService(mode: .granted),
            owner: MockSeeds.owner,
            initialDogs: MockSeeds.demoDogs
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
    let permissionService: any MediaPermissionServicing
    let owner: OwnerProfile

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
        permissionService = dependencies.permissionService
        owner = dependencies.owner
        dogs = dependencies.initialDogs
        selectedDogID = dependencies.initialDogs.first?.id
        hasCompletedOnboarding = UserDefaults.standard.bool(forKey: Self.onboardingKey)
        appearanceMode = AppearanceMode(rawValue: UserDefaults.standard.string(forKey: Self.appearanceKey) ?? "") ?? .system
    }

    convenience init() {
        self.init(dependencies: .demo)
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