import SwiftUI

struct BarklyDogHeroView: View {
    var size: CGFloat = 300

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.colorScheme) private var colorScheme
    @State private var breathing = false
    @State private var blink = false
    @State private var isCheering = false

    var body: some View {
        ZStack {
            Ellipse()
                .fill(BarklyColor.primaryText.opacity(colorScheme == .dark ? 0.14 : 0.06))
                .frame(width: size * 0.70, height: size * 0.07)
                .offset(y: size * 0.46)
                .accessibilityHidden(true)

            BarklyDogPortrait(isBlinking: blink)
                .frame(width: size, height: size)
                .scaleEffect(breathing ? 1.02 : 1.0)
                .scaleEffect(isCheering ? 1.06 : 1.0)
                .animation(reduceMotion ? nil : .easeInOut(duration: 2.4).repeatForever(autoreverses: true), value: breathing)
                .animation(.spring(response: 0.34, dampingFraction: 0.55), value: isCheering)
                .onAppear {
                    breathing = true
                }
        }
        .frame(width: size, height: size)
        .accessibilityElement(children: .contain)
        .accessibilityLabel("BARKLY dog")
        .task {
            guard !reduceMotion else { return }
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: UInt64.random(in: 2_600_000_000...6_000_000_000))
                guard !Task.isCancelled else { break }
                withAnimation(.easeInOut(duration: 0.12)) { blink = true }
                try? await Task.sleep(nanoseconds: 170_000_000)
                guard !Task.isCancelled else { break }
                withAnimation(.easeInOut(duration: 0.12)) { blink = false }
            }
        }
    }

    func cheer() {
        guard !isCheering else { return }
        isCheering = true
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: 380_000_000)
            isCheering = false
        }
    }
}

struct BarklyDogPortrait: View {
    var isBlinking: Bool

    var body: some View {
        GeometryReader { geometry in
            let w = geometry.size.width
            let h = geometry.size.height

            ZStack {
                decorationEar(
                    flipped: false,
                    offsetX: -w * 0.28,
                    rotation: 16,
                    size: CGSize(width: w * 0.31, height: h * 0.50)
                )
                decorationEar(
                    flipped: true,
                    offsetX: w * 0.28,
                    rotation: -16,
                    size: CGSize(width: w * 0.31, height: h * 0.50)
                )

                head(w: w, h: h)
                cheeks(w: w, h: h)
                chest(w: w, h: h)
                collar(w: w, h: h)
                collarTag(w: w, h: h)
                muzzle(w: w, h: h)
                eyes(w: w, h: h)
                eyelids(w: w, h: h)
                brows(w: w, h: h)
                nose(w: w, h: h)
                mouth(w: w, h: h)
            }
            .frame(width: w, height: h)
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityHidden(true)
    }

    private func decorationEar(flipped: Bool, offsetX: CGFloat, rotation: Double, size: CGSize) -> some View {
        Ellipse()
            .fill(Color.furDeep)
            .frame(width: size.width, height: size.height)
            .rotationEffect(.degrees(rotation * (flipped ? 1 : -1)))
            .offset(x: offsetX, y: 0)
    }

    private func head(w: CGFloat, h: CGFloat) -> some View {
        RoundedRectangle(cornerRadius: w * 0.30, style: .continuous)
            .fill(Color.furBase)
            .frame(width: w * 0.82, height: h * 0.66)
            .position(x: w * 0.5, y: h * 0.40)
    }

    private func cheeks(w: CGFloat, h: CGFloat) -> some View {
        ZStack {
            Ellipse()
                .fill(Color.furBase)
                .frame(width: w * 0.30, height: h * 0.32)
                .position(x: w * 0.22, y: h * 0.48)
            Ellipse()
                .fill(Color.furBase)
                .frame(width: w * 0.30, height: h * 0.32)
                .position(x: w * 0.78, y: h * 0.48)
        }
    }

    private func chest(w: CGFloat, h: CGFloat) -> some View {
        Ellipse()
            .fill(Color.muzzleCream)
            .frame(width: w * 0.54, height: h * 0.32)
            .position(x: w * 0.5, y: h * 0.96)
    }

    private func collar(w: CGFloat, h: CGFloat) -> some View {
        RoundedRectangle(cornerRadius: w * 0.05, style: .continuous)
            .fill(BarklyColor.cosmicOrange)
            .frame(width: w * 0.60, height: h * 0.11)
            .position(x: w * 0.5, y: h * 0.80)
    }

    private func collarTag(w: CGFloat, h: CGFloat) -> some View {
        ZStack {
            Circle()
                .fill(Color.white)
                .frame(width: w * 0.10, height: w * 0.10)
                .overlay(Circle().stroke(BarklyColor.cosmicOrange.opacity(0.35), lineWidth: w * 0.012))
            Text("B")
                .font(.system(size: w * 0.055, weight: .heavy, design: .rounded))
                .foregroundStyle(BarklyColor.cosmicOrangeDeep)
        }
        .position(x: w * 0.5, y: h * 0.88)
    }

    private func muzzle(w: CGFloat, h: CGFloat) -> some View {
        Ellipse()
            .fill(Color.muzzleCream)
            .frame(width: w * 0.36, height: h * 0.28)
            .position(x: w * 0.5, y: h * 0.64)
    }

    private func eyes(w: CGFloat, h: CGFloat) -> some View {
        ZStack {
            EyeShape()
                .fill(Color.dogDark)
                .frame(width: w * 0.075, height: h * 0.10)
                .overlay(glint(w: w, h: h).offset(x: -w * 0.012, y: -h * 0.016))
                .position(x: w * 0.38, y: h * 0.42)
            EyeShape()
                .fill(Color.dogDark)
                .frame(width: w * 0.075, height: h * 0.10)
                .overlay(glint(w: w, h: h).offset(x: -w * 0.012, y: -h * 0.016))
                .position(x: w * 0.62, y: h * 0.42)
        }
    }

    private func glint(w: CGFloat, h: CGFloat) -> some View {
        Circle()
            .fill(Color.white)
            .frame(width: w * 0.018, height: w * 0.018)
    }

    private func eyelids(w: CGFloat, h: CGFloat) -> some View {
        ZStack {
            eyelid(w: w, h: h)
                .position(x: w * 0.38, y: h * 0.42)
            eyelid(w: w, h: h)
                .position(x: w * 0.62, y: h * 0.42)
        }
    }

    private func eyelid(w: CGFloat, h: CGFloat) -> some View {
        RoundedRectangle(cornerRadius: w * 0.03, style: .continuous)
            .fill(Color.furBase)
            .frame(width: w * 0.085, height: h * 0.10)
            .scaleEffect(y: isBlinking ? 1.0 : 0.03, anchor: .center)
            .opacity(isBlinking ? 1 : 0)
    }

    private func brows(w: CGFloat, h: CGFloat) -> some View {
        ZStack {
            Capsule()
                .fill(Color.furDeep)
                .frame(width: w * 0.13, height: h * 0.020)
                .rotationEffect(.degrees(-6))
                .position(x: w * 0.38, y: h * 0.335)
            Capsule()
                .fill(Color.furDeep)
                .frame(width: w * 0.13, height: h * 0.020)
                .rotationEffect(.degrees(-174))
                .position(x: w * 0.62, y: h * 0.335)
        }
    }

    private func nose(w: CGFloat, h: CGFloat) -> some View {
        RoundedRectangle(cornerRadius: w * 0.025, style: .continuous)
            .fill(Color.dogDark)
            .frame(width: w * 0.115, height: h * 0.065)
            .position(x: w * 0.5, y: h * 0.50)
    }

    private func mouth(w: CGFloat, h: CGFloat) -> some View {
        Path { path in
            let centerY = h * 0.545
            path.move(to: CGPoint(x: w * 0.5, y: centerY))
            path.addQuadCurve(
                to: CGPoint(x: w * 0.5, y: centerY + h * 0.045),
                control: CGPoint(x: w * 0.5, y: centerY + h * 0.032)
            )
            path.move(to: CGPoint(x: w * 0.5, y: centerY + h * 0.045))
            path.addQuadCurve(
                to: CGPoint(x: w * 0.39, y: centerY + h * 0.058),
                control: CGPoint(x: w * 0.5, y: centerY + h * 0.078)
            )
            path.move(to: CGPoint(x: w * 0.5, y: centerY + h * 0.045))
            path.addQuadCurve(
                to: CGPoint(x: w * 0.61, y: centerY + h * 0.058),
                control: CGPoint(x: w * 0.5, y: centerY + h * 0.078)
            )
        }
        .stroke(Color.dogDark, style: StrokeStyle(lineWidth: w * 0.011, lineCap: .round, lineJoin: .round))
    }
}

private struct EyeShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.move(to: CGPoint(x: rect.minX + rect.width * 0.5, y: rect.minY))
        path.addQuadCurve(
            to: CGPoint(x: rect.maxX, y: rect.midY),
            control: CGPoint(x: rect.minX + rect.width * 0.85, y: rect.minY + rect.height * 0.08)
        )
        path.addQuadCurve(
            to: CGPoint(x: rect.minX + rect.width * 0.5, y: rect.maxY),
            control: CGPoint(x: rect.minX + rect.width * 0.85, y: rect.maxY - rect.height * 0.08)
        )
        path.addQuadCurve(
            to: CGPoint(x: rect.minX, y: rect.midY),
            control: CGPoint(x: rect.minX + rect.width * 0.15, y: rect.maxY - rect.height * 0.08)
        )
        path.addQuadCurve(
            to: CGPoint(x: rect.minX + rect.width * 0.5, y: rect.minY),
            control: CGPoint(x: rect.minX + rect.width * 0.15, y: rect.minY + rect.height * 0.08)
        )
        path.closeSubpath()
        return path
    }
}

private extension Color {
    static let furBase = Color(red: 0.96, green: 0.78, blue: 0.56)
    static let furDeep = Color(red: 0.77, green: 0.52, blue: 0.30)
    static let muzzleCream = Color(red: 1.00, green: 0.97, blue: 0.92)
    static let dogDark = Color(red: 0.24, green: 0.19, blue: 0.16)
}