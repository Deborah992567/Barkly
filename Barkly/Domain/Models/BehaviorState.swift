import Foundation

enum BehaviorState: String, Codable, CaseIterable, Sendable {
    case calm
    case playful
    case excited
    case alert
    case curious
    case anxious
    case fearful
    case attentionSeeking
    case potentiallyThreatening
    case unknown

    var shortName: String {
        switch self {
        case .calm: "Calm"
        case .playful: "Playful"
        case .excited: "Excited"
        case .alert: "Alert"
        case .curious: "Curious"
        case .anxious: "Anxious"
        case .fearful: "Fearful"
        case .attentionSeeking: "Attention-seeking"
        case .potentiallyThreatening: "Warning signals"
        case .unknown: "Unknown"
        }
    }

    var estimatedTitle: String {
        switch self {
        case .calm: "Likely calm and comfortable"
        case .playful: "Likely in a playful mood"
        case .excited: "Likely excited"
        case .alert: "Likely alert and watching intently"
        case .curious: "Likely curious about something new"
        case .anxious: "Likely feeling anxious"
        case .fearful: "Likely feeling fearful"
        case .attentionSeeking: "Likely seeking attention"
        case .potentiallyThreatening: "Showing possible warning signals"
        case .unknown: "BARKLY couldn't estimate this one"
        }
    }

    var summary: String {
        switch self {
        case .calm: "A relaxed, even posture with soft movement. Signals like a loose tail and gentle breathing suggest comfort."
        case .playful: "Wiggly, bouncy movement and a play bow. Quick direction changes and an open mouth suggest interest in play."
        case .excited: "Fast, short movements and loud vocalizations. Elevated energy can mean positive excitement or overstimulation."
        case .alert: "A fixed stare, pricked ears, and a still body. Something nearby may be holding your dog's full attention."
        case .curious: "Head tilts, forward ears, and sniffing. Your dog is gathering information about something unfamiliar."
        case .anxious: "Tension and restless pacing. Whining, lip licking, and a tucked tail can be early signs of unease."
        case .fearful: "Closed body language, flattened ears, and avoidance. Your dog is signaling that it wants the distance to increase."
        case .attentionSeeking: "Repeated vocalization and movement toward you. Your dog is trying to start a specific interaction."
        case .potentiallyThreatening: "Rigid posture, hard stare, and growling. Give your dog space and remove the trigger if safe to do so."
        case .unknown: "The available signals weren't clear enough to estimate. Try capturing more of the moment next time."
        }
    }
}