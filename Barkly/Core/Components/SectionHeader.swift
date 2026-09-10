import SwiftUI

struct SectionHeader: View {
    let title: String
    var subtitle: String? = nil
    var trailing: String? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(alignment: .firstTextBaseline, spacing: BarklySpacing.sm) {
                Text(title)
                    .font(BarklyFont.sectionHeader)
                    .foregroundStyle(BarklyColor.primaryText)
                if let trailing {
                    Text(trailing)
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.tertiaryText)
                }
                Spacer(minLength: 0)
            }
            if let subtitle {
                Text(subtitle)
                    .font(BarklyFont.footnote)
                    .foregroundStyle(BarklyColor.secondaryText)
            }
        }
        .accessibilityElement(children: .combine)
    }
}