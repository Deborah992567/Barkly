import SwiftUI
import CoreGraphics

enum BarklySpacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 16
    static let lg: CGFloat = 24
    static let xl: CGFloat = 32
    static let xxl: CGFloat = 48

    static let pagePadding: CGFloat = 20
    static let cardPadding: CGFloat = 20
    static let sectionGap: CGFloat = 24
    static let itemGap: CGFloat = 12
}

enum BarklyRadius {
    static let small: CGFloat = 10
    static let card: CGFloat = 20
    static let large: CGFloat = 28
    static let pill: CGFloat = 999
}

enum BarklyShadow {
    static let card = Color.black.opacity(0.05)
    static let cardRadius: CGFloat = 16
    static let cardY: CGFloat = 2
}