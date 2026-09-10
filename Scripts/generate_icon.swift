#!/usr/bin/env swift
// Generates the BARKLY app icon (1024x1024 PNG) using SwiftUI/CoreGraphics.
import AppKit
import CoreGraphics
import Foundation
import ImageIO

let size = 1024
let S = CGFloat(size)

let colorSpace = CGColorSpace(name: CGColorSpace.sRGB)!

func ctx() -> CGContext {
    let c = CGContext(data: nil, width: size, height: size, bitsPerComponent: 8,
                      bytesPerRow: 0, space: colorSpace,
                      bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    c.setShouldAntialias(true)
    c.setAllowsAntialiasing(true)
    return c
}

func rr(_ c: CGContext, _ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat, _ r: CGFloat) {
    c.addPath(CGPath(roundedRect: CGRect(x: x, y: y, width: w, height: h), cornerWidth: r, cornerHeight: r, transform: nil))
}

func fill(_ c: CGContext, _ path: CGPath, _ col: (CGFloat, CGFloat, CGFloat, CGFloat)) {
    c.addPath(path)
    c.setFillColor(CGColor(colorSpace: colorSpace, components: [col.0, col.1, col.2, col.3])!)
    c.fillPath()
}

func fillRect(_ c: CGContext, _ r: CGRect, _ col: (CGFloat, CGFloat, CGFloat, CGFloat)) {
    c.setFillColor(CGColor(colorSpace: colorSpace, components: [col.0, col.1, col.2, col.3])!)
    c.fill(r)
}

func fillEllipse(_ c: CGContext, _ r: CGRect, _ col: (CGFloat, CGFloat, CGFloat, CGFloat)) {
    c.setFillColor(CGColor(colorSpace: colorSpace, components: [col.0, col.1, col.2, col.3])!)
    c.fillEllipse(in: r)
}

let CREAM: (CGFloat, CGFloat, CGFloat, CGFloat) = (0.992, 0.965, 0.937, 1.0)
let ORANGE: (CGFloat, CGFloat, CGFloat, CGFloat) = (0.933, 0.416, 0.231, 1.0)
let ORANGE_DEEP: (CGFloat, CGFloat, CGFloat, CGFloat) = (0.78, 0.33, 0.16, 1.0)
let FUR: (CGFloat, CGFloat, CGFloat, CGFloat) = (0.96, 0.78, 0.56, 1.0)
let FUR_DEEP: (CGFloat, CGFloat, CGFloat, CGFloat) = (0.79, 0.55, 0.33, 1.0)
let DARK: (CGFloat, CGFloat, CGFloat, CGFloat) = (0.24, 0.19, 0.16, 1.0)

let c = ctx()

// Background
fillRect(c, CGRect(x: 0, y: 0, width: S, height: S), CREAM)

// Orange backing card with rounded corners
let card = CGRect(x: S*0.05, y: S*0.08, width: S*0.90, height: S*0.84)
fill(c, CGPath(roundedRect: card, cornerWidth: S*0.14, cornerHeight: S*0.14, transform: nil), ORANGE)

// Subtle shadow ring on card
c.setStrokeColor(CGColor(colorSpace: colorSpace, components: [1, 1, 1, 0.9])!)
c.setLineWidth(S*0.012)
c.addPath(CGPath(roundedRect: card.insetBy(dx: S*0.012, dy: S*0.012), cornerWidth: S*0.13, cornerHeight: S*0.13, transform: nil))
c.strokePath()

// --- Dog face ---
// Outer ears
fillEllipse(c, CGRect(x: S*0.09, y: S*0.42, width: S*0.26, height: S*0.40), FUR_DEEP)
fillEllipse(c, CGRect(x: S*0.65, y: S*0.42, width: S*0.26, height: S*0.40), FUR_DEEP)

// Head
fillEllipse(c, CGRect(x: S*0.27, y: S*0.33, width: S*0.46, height: S*0.56), FUR)

// Inner ear shading
fillEllipse(c, CGRect(x: S*0.16, y: S*0.48, width: S*0.12, height: S*0.20), ORANGE_DEEP)
fillEllipse(c, CGRect(x: S*0.72, y: S*0.48, width: S*0.12, height: S*0.20), ORANGE_DEEP)

// Muzzle
fillEllipse(c, CGRect(x: S*0.35, y: S*0.17, width: S*0.30, height: S*0.32), CREAM)

// Nose
fillEllipse(c, CGRect(x: S*0.448, y: S*0.285, width: S*0.10, height: S*0.07), DARK)

// Eyes
let eyeY = S*0.585
let eyeSize = S*0.048
fillEllipse(c, CGRect(x: S*0.355, y: eyeY - eyeSize/2, width: eyeSize, height: eyeSize), DARK)
fillEllipse(c, CGRect(x: S*0.595, y: eyeY - eyeSize/2, width: eyeSize, height: eyeSize), DARK)

// Mouth
let mouth = CGMutablePath()
mouth.move(to: CGPoint(x: S*0.47, y: S*0.44))
mouth.addQuadCurve(to: CGPoint(x: S*0.53, y: S*0.44), control: CGPoint(x: S*0.50, y: S*0.405))
c.addPath(mouth)
c.setStrokeColor(CGColor(colorSpace: colorSpace, components: [DARK.0, DARK.1, DARK.2, DARK.3])!)
c.setLineWidth(S*0.011)
c.setLineCap(.round)
c.strokePath()

// Collar ribbon at bottom
fill(c, CGPath(roundedRect: CGRect(x: S*0.30, y: S*0.06, width: S*0.40, height: S*0.09),
               cornerWidth: S*0.02, cornerHeight: S*0.02, transform: nil), ORANGE_DEEP)

let image = c.makeImage()!
let pngData = NSBitmapImageRep(cgImage: image).representation(using: .png, properties: [:])!

let repo = URL(fileURLWithPath: #file).deletingLastPathComponent().deletingLastPathComponent()
let outURL = repo
    .appendingPathComponent("Barkly/Resources/Assets.xcassets/AppIcon.appiconset")
    .appendingPathComponent("AppIcon.png")
try! pngData.write(to: outURL)
print("Wrote", outURL.path)