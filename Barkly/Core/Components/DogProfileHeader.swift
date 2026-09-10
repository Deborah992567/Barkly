import SwiftUI

struct DogProfileHeader: View {
    let dog: Dog
    var action: (() -> Void)? = nil

    var body: some View {
        HStack(spacing: BarklySpacing.md) {
            DogAvatar(dog: dog, size: 60)
            VStack(alignment: .leading, spacing: 2) {
                Text(dog.name)
                    .font(BarklyFont.cardTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                Text("\(dog.breed) \u{00B7} \(dog.ageDescription)")
                    .font(BarklyFont.subheadline)
                    .foregroundStyle(BarklyColor.secondaryText)
            }
            Spacer(minLength: BarklySpacing.sm)
            if let action {
                HStack(spacing: BarklySpacing.xs) {
                    Text("Switch")
                        .font(BarklyFont.label)
                    Image(systemName: "chevron.up.chevron.down")
                        .font(.system(size: 12, weight: .semibold))
                }
                .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                .padding(.horizontal, BarklySpacing.md)
                .frame(minHeight: 36)
                .background(BarklyColor.cosmicOrangeSoft, in: Capsule())
                .contentShape(Capsule())
                .onTapGesture(perform: action)
                .accessibilityElement(children: .combine)
                .accessibilityLabel("Switch \(dog.name)")
                .accessibilityHint("Opens the dog selector")
            }
        }
    }
}