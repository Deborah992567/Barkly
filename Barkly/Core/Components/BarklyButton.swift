import SwiftUI

struct BarklyButton: View {
    enum Style {
        case primary
        case secondary
        case tinted
        case destructive
    }

    let title: String
    var icon: String? = nil
    var style: Style = .primary
    var action: () -> Void

    var body: some View {
        Button(action: perform) {
            HStack(spacing: BarklySpacing.sm) {
                if let icon {
                    Image(systemName: icon)
                        .font(.system(size: 17, weight: .semibold))
                }
                Text(title)
                    .font(BarklyFont.button)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            .foregroundStyle(foreground)
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .background(background, in: Capsule())
            .overlay {
                if style == .secondary {
                    Capsule().strokeBorder(BarklyColor.divider, lineWidth: 1)
                }
            }
            .contentShape(Capsule())
        }
        .buttonStyle(BarklyButtonPressStyle())
        .accessibilityLabel(title)
    }

    private func perform() {
        Haptics.light()
        action()
    }

    private var foreground: Color {
        switch style {
        case .primary: BarklyColor.onCosmicOrange
        case .secondary: BarklyColor.primaryText
        case .tinted: BarklyColor.cosmicOrangeDeep
        case .destructive: BarklyColor.onCosmicOrange
        }
    }

    private var background: AnyShapeStyle {
        switch style {
        case .primary: return AnyShapeStyle(BarklyColor.cosmicOrange)
        case .secondary: return AnyShapeStyle(BarklyColor.surface)
        case .tinted: return AnyShapeStyle(BarklyColor.cosmicOrangeSoft)
        case .destructive: return AnyShapeStyle(BarklyColor.error)
        }
    }
}

private struct BarklyButtonPressStyle: ButtonStyle {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(reduceMotion ? 1 : (configuration.isPressed ? 0.98 : 1))
            .opacity(configuration.isPressed ? 0.92 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}