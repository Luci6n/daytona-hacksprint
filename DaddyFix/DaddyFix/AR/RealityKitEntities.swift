//
//  RealityKitEntities.swift
//  DaddyFix
//
//  Brian — RealityKit visual entities for repair annotations.
//

import RealityKit
import UIKit
import simd

enum RealityKitEntities {
    /// Builds a visual entity for a backend/mock ARAnnotation.
    static func makeEntity(for annotation: ARAnnotation) -> ModelEntity {
        switch annotation.type.lowercased() {
        case "arrow":
            return makeArrow(label: annotation.label, color: color(from: annotation.color, fallback: .systemTeal))
        case "circle":
            return makeCircle(label: annotation.label, color: color(from: annotation.color, fallback: .systemGreen))
        case "text":
            return makeTextLabel(annotation.label, color: color(from: annotation.color, fallback: .white))
        case "highlight":
            fallthrough
        default:
            let w = Float(annotation.width ?? 0.12)
            let h = Float(annotation.height ?? 0.08)
            return makeHighlight(
                width: max(w, 0.06),
                height: max(h, 0.04),
                label: annotation.label,
                color: color(from: annotation.color, fallback: .systemGreen)
            )
        }
    }

    // MARK: - Primitives

    /// Soft glowing box that sits on the part surface (ELCB highlight).
    static func makeHighlight(
        width: Float,
        height: Float,
        label: String,
        color: UIColor
    ) -> ModelEntity {
        let depth: Float = 0.01
        let mesh = MeshResource.generateBox(size: [width, height, depth])
        let material = SimpleMaterial(
            color: color.withAlphaComponent(0.45),
            roughness: 0.25,
            isMetallic: false
        )

        let box = ModelEntity(mesh: mesh, materials: [material])
        box.name = "highlight:\(label)"
        box.generateCollisionShapes(recursive: true)

        // Thin border plate for readability against busy appliance panels.
        let borderMesh = MeshResource.generateBox(size: [width + 0.004, height + 0.004, 0.002])
        let borderMat = UnlitMaterial(color: color.withAlphaComponent(0.95))
        let border = ModelEntity(mesh: borderMesh, materials: [borderMat])
        border.position = SIMD3(0, 0, 0.006)
        box.addChild(border)

        let tag = makeTextLabel(label, color: .white, fontSize: 0.03)
        tag.position = SIMD3(0, height * 0.5 + 0.04, 0.02)
        box.addChild(tag)

        return box
    }

    /// Simple “arrow” pointing down toward the part (cone + shaft).
    static func makeArrow(label: String, color: UIColor) -> ModelEntity {
        let root = ModelEntity()
        root.name = "arrow:\(label)"

        let shaftMesh = MeshResource.generateBox(size: [0.012, 0.08, 0.012])
        let shaftMat = SimpleMaterial(color: color, isMetallic: false)
        let shaft = ModelEntity(mesh: shaftMesh, materials: [shaftMat])
        shaft.position = SIMD3(0, 0.06, 0)

        // Pyramid-ish tip (scaled box) pointing -Y toward the appliance — works on all RealityKit versions.
        let tipMesh = MeshResource.generateBox(size: [0.045, 0.045, 0.045])
        let tipMat = SimpleMaterial(color: color, isMetallic: false)
        let tip = ModelEntity(mesh: tipMesh, materials: [tipMat])
        tip.orientation = simd_quatf(angle: .pi / 4, axis: SIMD3(0, 0, 1))
        tip.position = SIMD3(0, 0.015, 0)
        tip.scale = SIMD3(1, 0.55, 1)

        root.addChild(shaft)
        root.addChild(tip)
        root.generateCollisionShapes(recursive: true)

        // Gentle float above the hit surface so it stays visible.
        root.position = SIMD3(0, 0.12, 0)
        return root
    }

    static func makeCircle(label: String, color: UIColor) -> ModelEntity {
        let mesh = MeshResource.generateCylinder(height: 0.005, radius: 0.05)
        let material = UnlitMaterial(color: color.withAlphaComponent(0.7))
        let entity = ModelEntity(mesh: mesh, materials: [material])
        entity.name = "circle:\(label)"
        entity.generateCollisionShapes(recursive: true)

        let tag = makeTextLabel(label, color: .white, fontSize: 0.025)
        tag.position = SIMD3(0, 0.04, 0)
        entity.addChild(tag)
        return entity
    }

    /// Billboarding-ish text plate (fixed orientation; good enough for demo).
    static func makeTextLabel(
        _ text: String,
        color: UIColor,
        fontSize: CGFloat = 0.035
    ) -> ModelEntity {
        let mesh = MeshResource.generateText(
            text,
            extrusionDepth: 0.002,
            font: .systemFont(ofSize: fontSize, weight: .semibold),
            containerFrame: .zero,
            alignment: .center,
            lineBreakMode: .byWordWrapping
        )
        let material = UnlitMaterial(color: color)
        let entity = ModelEntity(mesh: mesh, materials: [material])
        entity.name = "text:\(text)"

        // Center the text mesh roughly on its anchor.
        let bounds = entity.visualBounds(relativeTo: nil)
        entity.position = SIMD3(
            -bounds.center.x,
            -bounds.center.y,
            0
        )
        return entity
    }

    /// Debug sphere for raycast testing.
    static func makeDebugSphere(color: UIColor = .systemOrange, radius: Float = 0.02) -> ModelEntity {
        let mesh = MeshResource.generateSphere(radius: radius)
        let material = SimpleMaterial(color: color, isMetallic: false)
        let entity = ModelEntity(mesh: mesh, materials: [material])
        entity.name = "debugSphere"
        entity.generateCollisionShapes(recursive: true)
        return entity
    }

    // MARK: - Color helpers

    static func color(from raw: String?, fallback: UIColor) -> UIColor {
        guard let raw, !raw.isEmpty else { return fallback }
        if raw.hasPrefix("#") {
            return UIColor(hex: raw) ?? fallback
        }
        switch raw.lowercased() {
        case "green": return .systemGreen
        case "blue", "teal": return .systemTeal
        case "red": return .systemRed
        case "orange": return .systemOrange
        case "white": return .white
        case "yellow": return .systemYellow
        default: return fallback
        }
    }
}

// MARK: - UIColor hex

private extension UIColor {
    convenience init?(hex: String) {
        var s = hex.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        if s.hasPrefix("#") { s.removeFirst() }
        guard s.count == 6 || s.count == 8 else { return nil }

        var value: UInt64 = 0
        guard Scanner(string: s).scanHexInt64(&value) else { return nil }

        let a, r, g, b: CGFloat
        if s.count == 8 {
            a = CGFloat((value & 0xFF00_0000) >> 24) / 255
            r = CGFloat((value & 0x00FF_0000) >> 16) / 255
            g = CGFloat((value & 0x0000_FF00) >> 8) / 255
            b = CGFloat(value & 0x0000_00FF) / 255
        } else {
            a = 1
            r = CGFloat((value & 0xFF0000) >> 16) / 255
            g = CGFloat((value & 0x00FF00) >> 8) / 255
            b = CGFloat(value & 0x0000FF) / 255
        }
        self.init(red: r, green: g, blue: b, alpha: a)
    }
}
