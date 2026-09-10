import XCTest
import SwiftUI
@testable import Barkly

final class DomainModelTests: XCTestCase {

    private func makeDog(
        name: String = "Max",
        breed: String = "Golden Retriever",
        yearsAgo: Int = 3
    ) -> Dog {
        Dog(
            name: name,
            breed: breed,
            dateOfBirth: Calendar.current.date(byAdding: .year, value: -yearsAgo, to: Date()) ?? Date()
        )
    }

    private func makeAnalysis(
        dogID: UUID,
        state: BehaviorState = .calm,
        confidence: Float = 0.8,
        inputType: AnalysisInputType = .audio,
        createdAt: Date = Date()
    ) -> BehaviorAnalysis {
        BehaviorAnalysis(
            dogID: dogID,
            createdAt: createdAt,
            inputType: inputType,
            vocalizationType: .bark,
            estimatedState: state,
            confidence: confidence,
            observations: ["Signal one", "Signal two"],
            explanation: "A test explanation."
        )
    }

    func testDogAgeDescription() {
        let dog = makeDog(yearsAgo: 3)
        XCTAssertTrue(dog.ageDescription.contains("3 year"))
        XCTAssertEqual(dog.ageDescription, "3 years old")
    }

    func testDogAgeForPuppyUsesMonths() {
        let puppy = Dog(
            name: "Pip",
            breed: "Corgi",
            dateOfBirth: Calendar.current.date(byAdding: .month, value: -5, to: Date()) ?? Date()
        )
        XCTAssertTrue(puppy.ageDescription.contains("month"))
    }

    func testBehaviorAnalysisConfidencePercent() {
        let analysis = makeAnalysis(dogID: UUID(), confidence: 0.835)
        XCTAssertEqual(analysis.confidencePercent, 84)
    }

    func testBehaviorStateEstimatedTitleAndSummary() {
        XCTAssertEqual(BehaviorState.calm.estimatedTitle, "Likely calm and comfortable")
        XCTAssertEqual(BehaviorState.playful.summary, "Wiggly, bouncy movement and a play bow. Quick direction changes and an open mouth suggest interest in play.")
        XCTAssertEqual(BehaviorState.attentionSeeking.estimatedTitle, "Likely seeking attention")
    }

    func testBehaviorStateAccentColorsDiffer() {
        XCTAssertNotEqual(BehaviorState.calm.accentColor, BehaviorState.excited.accentColor)
    }

    func testAnalysisInputTypeHelpers() {
        XCTAssertEqual(AnalysisInputType.audio.title, "Sound recording")
        XCTAssertEqual(AnalysisInputType.video.shortTitle, "Video")
        XCTAssertEqual(AnalysisInputType.photo.symbolName, "photo.fill")
        XCTAssertEqual(AnalysisInputType.behavior.symbolName, "eye.fill")
    }

    func testVocalizationDisplayNames() {
        XCTAssertEqual(VocalizationType.bark.displayName, "Bark")
        XCTAssertEqual(VocalizationType.silence.displayName, "Silence")
    }

    func testTimeOfDayDisplayNames() {
        XCTAssertEqual(TimeOfDay.morning.displayName, "Morning")
        XCTAssertEqual(TimeOfDay.night.displayName, "Night")
    }
}