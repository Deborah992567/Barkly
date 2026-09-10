import SwiftUI

struct ConfidenceRing: View {
    let confidence: Float

    private var percent: Int {
        Int((confidence * 100).rounded())
    }

    var body: some View {
        ZStack {
            Circle()
                .stroke(BarklyColor.cosmicOrangeSoft, lineWidth: 10)
            Circle()
                .trim(from: 0, to: CGFloat(confidence))
                .stroke(
                    BarklyColor.cosmicOrange,
                    style: StrokeStyle(lineWidth: 10, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
            VStack(spacing: 2) {
                Text("\(percent)%")
                    .font(.system(size: 24, weight: .bold, design: .rounded))
                    .foregroundStyle(BarklyColor.primaryText)
                Text("confidence")
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.secondaryText)
            }
        }
        .frame(width: 118, height: 118)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("BARKLY confidence \(percent) percent")
    }
}