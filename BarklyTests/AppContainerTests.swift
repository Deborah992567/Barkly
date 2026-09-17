import XCTest
@testable import Barkly

@MainActor
final class AppContainerTests: XCTestCase {

    override func setUp() {
        super.setUp()
        UserDefaults.standard.removeObject(forKey: "barkly.hasCompletedOnboarding")
        UserDefaults.standard.removeObject(forKey: "barkly.appearanceMode")
    }

    private func makeContainer() -> AppContainer {
        AppContainer(dependencies: .demo)
    }

    func testSelectsFirstDogByDefault() {
        let container = makeContainer()
        XCTAssertEqual(container.selectedDogID, MockSeeds.max.id)
        XCTAssertEqual(container.selectedDog?.name, "Max")
    }

    func testSelectDogSwitchesSelection() {
        let container = makeContainer()
        container.selectDog(id: MockSeeds.luna.id)
        XCTAssertEqual(container.selectedDogID, MockSeeds.luna.id)
        XCTAssertEqual(container.selectedDog?.breed, "German Shepherd")
    }

    func testCompleteOnboardingPersists() {
        let container = makeContainer()
        XCTAssertFalse(container.hasCompletedOnboarding)
        container.completeOnboarding()
        XCTAssertTrue(container.hasCompletedOnboarding)
        XCTAssertTrue(UserDefaults.standard.bool(forKey: "barkly.hasCompletedOnboarding"))
    }

    func testAppearanceModeRoundTrips() {
        let container = makeContainer()
        container.setAppearanceMode(.dark)
        XCTAssertEqual(container.appearanceMode, .dark)
        let reloaded = makeContainer()
        XCTAssertEqual(reloaded.appearanceMode, .dark)
    }

    func testUpdateDogReplacesValue() async throws {
        let container = makeContainer()
        var dog = MockSeeds.max
        dog.name = "Maxwell"
        let updated = try await container.updateDog(dog)
        XCTAssertEqual(updated.name, "Maxwell")
        XCTAssertEqual(container.dogs.first { $0.id == dog.id }?.name, "Maxwell")
    }

    func testAddDogAppendsAndSelectsServerDog() async throws {
        let container = makeContainer()
        let created = try await container.addDog(
            name: "Rex",
            breed: "Labrador",
            dateOfBirth: Date(),
            notes: "E2E"
        )
        XCTAssertEqual(container.dogs.map(\.id), [MockSeeds.max.id, MockSeeds.luna.id, created.id])
        XCTAssertEqual(container.selectedDogID, created.id)
    }

    func testLoadDogsRefreshesFromRepository() async throws {
        let container = makeContainer()
        try await container.addDog(name: "Rex", breed: nil, dateOfBirth: Date(), notes: nil)
        XCTAssertEqual(container.dogs.count, 3)
        try await container.loadDogs()
        XCTAssertEqual(container.dogs.count, 3)
    }
}