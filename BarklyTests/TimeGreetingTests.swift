import XCTest
@testable import Barkly

final class TimeGreetingTests: XCTestCase {

    private func date(hour: Int) -> Date {
        var components = DateComponents()
        components.calendar = Calendar.current
        components.hour = hour
        components.minute = 30
        return components.date ?? Date()
    }

    func testMorningHoursGreetMorning() {
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 5)), "Good morning")
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 11)), "Good morning")
    }

    func testAfternoonHoursGreetAfternoon() {
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 12)), "Good afternoon")
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 16)), "Good afternoon")
    }

    func testEveningHoursGreetEvening() {
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 17)), "Good evening")
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 21)), "Good evening")
    }

    func testNightHoursGreetEvening() {
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 22)), "Good evening")
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 0)), "Good evening")
        XCTAssertEqual(TimeGreeting.greeting(for: date(hour: 4)), "Good evening")
    }

    func testDefaultGreetingForNow() {
        XCTAssertFalse(TimeGreeting.greeting().isEmpty)
    }
}