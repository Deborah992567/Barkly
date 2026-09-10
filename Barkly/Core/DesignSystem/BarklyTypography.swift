import SwiftUI

enum BarklyFont {
    static var brand: Font {
        .system(size: 38, weight: .heavy, design: .rounded)
    }

    static var heroTitle: Font {
        .system(size: 28, weight: .bold, design: .rounded)
    }

    static var displayHeading: Font {
        .system(size: 24, weight: .bold, design: .rounded)
    }

    static var cardTitle: Font {
        .system(size: 19, weight: .semibold, design: .rounded)
    }

    static var button: Font {
        .system(size: 17, weight: .semibold, design: .rounded)
    }

    static var label: Font {
        .system(size: 15, weight: .medium, design: .rounded)
    }

    static var sectionHeader: Font {
        .system(size: 15, weight: .semibold, design: .rounded)
    }

    static var body: Font {
        .body
    }

    static var subheadline: Font {
        .subheadline
    }

    static var caption: Font {
        .caption
    }

    static var footnote: Font {
        .footnote
    }
}