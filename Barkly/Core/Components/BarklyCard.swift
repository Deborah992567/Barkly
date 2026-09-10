import SwiftUI

struct BarklyCard<Content: View>: View {
    var padding: CGFloat = BarklySpacing.cardPadding
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                    .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
            )
            .cardShadow()
    }
}