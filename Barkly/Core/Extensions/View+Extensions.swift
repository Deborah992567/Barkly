import SwiftUI

extension View {
    @ViewBuilder
    func `if`<Content: View>(_ condition: Bool, transform: (Self) -> Content) -> some View {
        if condition {
            transform(self)
        } else {
            self
        }
    }

    func ensureTouchTarget(minimum: CGFloat = 44) -> some View {
        frame(minWidth: minimum, minHeight: minimum)
    }

    func cardShadow() -> some View {
        shadow(color: BarklyShadow.card, radius: BarklyShadow.cardRadius, x: 0, y: BarklyShadow.cardY)
    }
}