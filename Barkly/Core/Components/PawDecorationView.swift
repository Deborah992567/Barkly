import SwiftUI

struct PawDecorationView: View {
    enum Corner {
        case topLeft
        case topRight
        case bottomLeft
        case bottomRight
    }

    var corner: Corner = .topLeft
    var size: CGFloat = 120
    var tint: Color = BarklyColor.cosmicOrange
    var opacity: Double = 1

    private var rotation: Double {
        switch corner {
        case .topLeft: -24
        case .topRight: 24
        case .bottomLeft: 144
        case .bottomRight: -156
        }
    }

    private var padding: CGFloat {
        switch corner {
        case .topLeft: 18
        case .topRight: -4
        case .bottomLeft: -2
        case .bottomRight: 8
        }
    }

    var body: some View {
        PawShape()
            .fill(tint.opacity(opacity))
            .frame(width: size, height: size)
            .rotationEffect(.degrees(rotation))
            .padding(padding)
    }
}

struct PawShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        let w = rect.width
        let h = rect.height

        let padRect = CGRect(
            x: rect.minX + w * 0.20,
            y: rect.minY + h * 0.48,
            width: w * 0.60,
            height: h * 0.50
        )
        path.addEllipse(in: padRect)

        let toeWidth = w * 0.22
        let toeHeight = h * 0.28
        let toes = [
            CGRect(x: rect.minX + w * 0.03, y: rect.minY + h * 0.12, width: toeWidth, height: toeHeight),
            CGRect(x: rect.minX + w * 0.27, y: rect.minY + h * 0.02, width: toeWidth, height: toeHeight),
            CGRect(x: rect.minX + w * 0.51, y: rect.minY + h * 0.02, width: toeWidth, height: toeHeight),
            CGRect(x: rect.minX + w * 0.75, y: rect.minY + h * 0.12, width: toeWidth, height: toeHeight)
        ]
        toes.forEach { path.addEllipse(in: $0) }
        return path
    }
}