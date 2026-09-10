import SwiftUI

struct AnalysisProcessingView: View {
    let caption: String

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pulse = false

    var body: some View {
        VStack(spacing: BarklySpacing.lg) {
            Spacer()
            ZStack {
                Circle()
                    .fill(BarklyColor.cosmicOrangeSoft)
                    .frame(width: 116, height: 116)
                Image(systemName: "waveform")
                    .font(.system(size: 40, weight: .medium))
                    .foregroundStyle(BarklyColor.cosmicOrangeDeep)
            }
            .scaleEffect(reduceMotion ? 1 : (pulse ? 1.06 : 1))
            .accessibilityHidden(true)

            VStack(spacing: BarklySpacing.sm) {
                Text("Analyzing")
                    .font(BarklyFont.heroTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                Text(caption)
                    .font(BarklyFont.body)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .multilineTextAlignment(.center)
            }

            HStack(spacing: 6) {
                ForEach(0..<3, id: \.self) { index in
                    Circle()
                        .fill(BarklyColor.cosmicOrange)
                        .frame(width: 8, height: 8)
                        .opacity(reduceMotion ? 1 : (pulse ? 0.35 : 1))
                        .animation(
                            reduceMotion ? nil : .easeInOut(duration: 0.7).repeatForever(autoreverses: true).delay(Double(index) * 0.16),
                            value: pulse
                        )
                }
            }
            .accessibilityHidden(true)

            processingCard
                .padding(.top, BarklySpacing.sm)

            Spacer()
        }
        .padding(.horizontal, BarklySpacing.pagePadding)
        .onAppear { pulse = true }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Analyzing \(caption)")
        .accessibilityIdentifier("processing_state")
    }

    private var processingCard: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            skeletonLine(width: 200)
            skeletonLine(width: 150)
            skeletonLine(width: 180)
        }
        .padding(BarklySpacing.cardPadding)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        .opacity(reduceMotion ? 1 : (pulse ? 0.7 : 1))
        .accessibilityHidden(true)
    }

    private func skeletonLine(width: CGFloat) -> some View {
        RoundedRectangle(cornerRadius: 4, style: .continuous)
            .fill(BarklyColor.disabled.opacity(0.55))
            .frame(maxWidth: width, minHeight: 12)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview("Processing") {
    AnalysisProcessingView(caption: "BARKLY is reading the signals")
}