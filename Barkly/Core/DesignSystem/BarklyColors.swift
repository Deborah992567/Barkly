import SwiftUI
import UIKit

enum BarklyColor {
    private static func adaptive(light: UIColor, dark: UIColor) -> Color {
        Color(uiColor: UIColor { traits in
            traits.userInterfaceStyle == .dark ? dark : light
        })
    }

    static let background = adaptive(
        light: UIColor(hex: 0xFFFFFF),
        dark: UIColor(hex: 0x0F0E0D)
    )

    static let surface = adaptive(
        light: UIColor(hex: 0xFAF6F1),
        dark: UIColor(hex: 0x171512)
    )

    static let elevatedSurface = adaptive(
        light: UIColor(hex: 0xFFFFFF),
        dark: UIColor(hex: 0x201C18)
    )

    static let primaryText = adaptive(
        light: UIColor(hex: 0x1D1A17),
        dark: UIColor(hex: 0xF5F2EE)
    )

    static let secondaryText = adaptive(
        light: UIColor(hex: 0x6D6459),
        dark: UIColor(hex: 0xB8AC9E)
    )

    static let tertiaryText = adaptive(
        light: UIColor(hex: 0xA39A8F),
        dark: UIColor(hex: 0x83786C)
    )

    static let cosmicOrange = adaptive(
        light: UIColor(hex: 0xEE6A3B),
        dark: UIColor(hex: 0xF27E53)
    )

    static let cosmicOrangeDeep = adaptive(
        light: UIColor(hex: 0xC74F24),
        dark: UIColor(hex: 0xFF8A5C)
    )

    static let cosmicOrangeSoft = adaptive(
        light: UIColor(hex: 0xFDEBE3),
        dark: UIColor(hex: 0x3A241B)
    )

    static let onCosmicOrange = Color.white

    static let success = adaptive(
        light: UIColor(hex: 0x2F9E6E),
        dark: UIColor(hex: 0x53C08C)
    )

    static let warning = adaptive(
        light: UIColor(hex: 0xC98A1B),
        dark: UIColor(hex: 0xE3AA45)
    )

    static let error = adaptive(
        light: UIColor(hex: 0xD64545),
        dark: UIColor(hex: 0xF07171)
    )

    static let info = adaptive(
        light: UIColor(hex: 0x3B82C4),
        dark: UIColor(hex: 0x6FA3DB)
    )

    static let divider = adaptive(
        light: UIColor(hex: 0xEDE7E0),
        dark: UIColor(hex: 0x2B2722)
    )

    static let disabled = adaptive(
        light: UIColor(hex: 0xDAD3CB),
        dark: UIColor(hex: 0x49433D)
    )
}

private extension UIColor {
    convenience init(hex: UInt32) {
        self.init(
            red: CGFloat((hex >> 16) & 0xFF) / 255,
            green: CGFloat((hex >> 8) & 0xFF) / 255,
            blue: CGFloat(hex & 0xFF) / 255,
            alpha: 1
        )
    }
}

extension BehaviorState {
    var accentColor: Color {
        switch self {
        case .calm: BarklyColor.success
        case .playful, .excited: BarklyColor.cosmicOrange
        case .alert, .curious: BarklyColor.info
        case .anxious, .fearful, .potentiallyThreatening: BarklyColor.warning
        case .attentionSeeking: BarklyColor.cosmicOrangeDeep
        case .unknown: BarklyColor.tertiaryText
        }
    }
}