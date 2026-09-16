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

    func testUpdateDogReplacesValue() async {
        let container = makeContainer()
        var dog = MockSeeds.max
        dog.name = "Maxwell"
        await container.updateDog(dog)
        XCTAssertEqual(container.dogs.first { $0.id == dog.id }?.name, "Maxwell")
    }
}