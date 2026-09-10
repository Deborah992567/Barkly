import Foundation

enum MockSeeds {
    static let max: Dog = Dog(
        id: UUID(uuidString: "11111111-1111-1111-1111-111111111111")!,
        name: "Max",
        breed: "Golden Retriever",
        dateOfBirth: Calendar.current.date(byAdding: DateComponents(year: -3, month: -2), to: Date()) ?? Date(),
        notes: "Bringing a rope toy along makes any walk better."
    )

    static let luna: Dog = Dog(
        id: UUID(uuidString: "22222222-2222-2222-2222-222222222222")!,
        name: "Luna",
        breed: "German Shepherd",
        dateOfBirth: Calendar.current.date(byAdding: DateComponents(year: -2, month: -5), to: Date()) ?? Date(),
        notes: "Very alert around new sounds; settles quickly indoors."
    )

    static let demoDogs: [Dog] = [max, luna]

    static let owner: OwnerProfile = OwnerProfile(
        id: UUID(uuidString: "33333333-3333-3333-3333-333333333333")!,
        name: "Alex Hughes",
        email: "alex@example.com",
        memberSince: Calendar.current.date(byAdding: DateComponents(month: -8), to: Date()) ?? Date()
    )

    static func demoAnalyses() -> [BehaviorAnalysis] {
        func daysAgo(_ days: Int, hour: Int, minute: Int = 0) -> Date {
            let day = Calendar.current.date(byAdding: .day, value: -days, to: Date()) ?? Date()
            return Calendar.current.date(bySettingHour: hour, minute: minute, second: 0, of: day) ?? day
        }

        return [
            BehaviorAnalysis(
                id: UUID(uuidString: "aaaaaaa1-0000-0000-0000-00000000000a")!,
                dogID: max.id,
                createdAt: daysAgo(0, hour: 19, minute: 42),
                inputType: .audio,
                vocalizationType: .bark,
                estimatedState: .attentionSeeking,
                confidence: 0.82,
                observations: [
                    "Repeated vocalization",
                    "Short intervals between sounds",
                    "Alert posture",
                    "Movement toward owner"
                ],
                explanation: "The repeated barks arrived in short, even bursts while facing your direction. That pairing of regular timing and forward posture most often appears when a dog is trying to start an interaction."
            ),
            BehaviorAnalysis(
                id: UUID(uuidString: "aaaaaaa2-0000-0000-0000-00000000000a")!,
                dogID: luna.id,
                createdAt: daysAgo(1, hour: 17, minute: 12),
                inputType: .video,
                vocalizationType: nil,
                estimatedState: .playful,
                confidence: 0.78,
                observations: [
                    "Loose, wiggly body",
                    "Play bow observed",
                    "Tail wagging broadly",
                    "Quick orientation shifts"
                ],
                explanation: "The video shows a low, wobbly play bow followed by short bursts of side-to-side movement. A relaxed, wiggly frame paired with bouncing is one of the clearest social signals for play."
            ),
            BehaviorAnalysis(
                id: UUID(uuidString: "aaaaaaa3-0000-0000-0000-00000000000a")!,
                dogID: max.id,
                createdAt: daysAgo(2, hour: 8, minute: 5),
                inputType: .photo,
                vocalizationType: nil,
                estimatedState: .calm,
                confidence: 0.74,
                observations: [
                    "Relaxed posture",
                    "Soft eye contact",
                    "Neutral tail position",
                    "Slow breathing"
                ],
                explanation: "Every visible signal in the photo is low-energy: a settled frame, soft gaze, and a tail resting at its natural height. Nothing in posture or expression suggests urgency."
            ),
            BehaviorAnalysis(
                id: UUID(uuidString: "aaaaaaa4-0000-0000-0000-00000000000a")!,
                dogID: luna.id,
                createdAt: daysAgo(3, hour: 21, minute: 33),
                inputType: .audio,
                vocalizationType: .whine,
                estimatedState: .anxious,
                confidence: 0.69,
                observations: [
                    "High-pitched, rising pitch",
                    "Pacing noted while sound continued",
                    "Restless weight shifting",
                    "Ears drawn slightly back"
                ],
                explanation: "The whine kept a steady, rising tone rather than the flat cadence of attention-seeking. Combined with restless pacing, tension is the more consistent reading."
            ),
            BehaviorAnalysis(
                id: UUID(uuidString: "aaaaaaa5-0000-0000-0000-00000000000a")!,
                dogID: max.id,
                createdAt: daysAgo(5, hour: 12, minute: 26),
                inputType: .behavior,
                vocalizationType: nil,
                estimatedState: .curious,
                confidence: 0.71,
                observations: [
                    "Head tilt",
                    "Ears forward",
                    "Sniffing intently",
                    "Focused attention"
                ],
                explanation: "Your notes describe a long head tilt and directed sniffing right as the noise started. Forward ears and a still body while gathering smell are classic curiosity behaviors."
            ),
            BehaviorAnalysis(
                id: UUID(uuidString: "aaaaaaa6-0000-0000-0000-00000000000a")!,
                dogID: luna.id,
                createdAt: daysAgo(6, hour: 10, minute: 8),
                inputType: .video,
                vocalizationType: nil,
                estimatedState: .excited,
                confidence: 0.76,
                observations: [
                    "Fast tail movement",
                    "Elevated, springy posture",
                    "Short excited vocalization",
                    "Rapid orientation toward door"
                ],
                explanation: "High energy throughout the clip: springy posture, fast tail, and a repeated look toward the door as footsteps approached. The direction of attention points to anticipation."
            )
        ]
    }
}