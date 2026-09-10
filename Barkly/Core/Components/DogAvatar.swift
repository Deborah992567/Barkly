import SwiftUI

struct DogAvatar: View {
    let dog: Dog
    var size: CGFloat = 56

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.28, style: .continuous)
                .fill(BarklyColor.cosmicOrangeSoft)
            Image(systemName: "pawprint.fill")
                .font(.system(size: size * 0.42, weight: .semibold))
                .foregroundStyle(BarklyColor.cosmicOrangeDeep)
        }
        .frame(width: size, height: size)
        .accessibilityHidden(true)
    }
}