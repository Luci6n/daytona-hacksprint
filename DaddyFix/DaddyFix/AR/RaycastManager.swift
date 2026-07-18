//
//  RaycastManager.swift
//  DaddyFix
//
//  Brian — screen/normalized → world raycasts + annotation placement.
//

import ARKit
import RealityKit
import UIKit
import simd

@MainActor
final class RaycastManager {
    /// Root entity that holds all placed annotations (easy clear).
    private let annotationRoot = Entity()
    private var placedAnchors: [AnchorEntity] = []
    private var labelToAnchor: [String: AnchorEntity] = [:]

    private(set) weak var arView: ARView?

    /// Called when user taps a placed annotation (label).
    var onAnnotationSelected: ((String) -> Void)?

    func attach(arView: ARView) {
        self.arView = arView
        // Placed annotations are added as individual world anchors (see placeAnnotation).
        // annotationRoot is reserved for optional grouping in later polish.
        if annotationRoot.parent == nil {
            let origin = AnchorEntity(world: matrix_identity_float4x4)
            origin.name = "AnnotationRootAnchor"
            origin.addChild(annotationRoot)
            arView.scene.addAnchor(origin)
        }
    }

    // MARK: - Public API (Lucian / integration)

    /// Place all annotations from vision/agent result.
    /// Uses normalized 0…1 image coords → screen → LiDAR/plane raycast → persistent anchors.
    func placeAnnotations(_ annotations: [ARAnnotation]) {
        clearAnnotations()
        for annotation in annotations {
            _ = placeAnnotation(annotation)
        }
    }

    @discardableResult
    func placeAnnotation(_ annotation: ARAnnotation) -> AnchorEntity? {
        guard let arView else { return nil }

        let viewSize = arView.bounds.size
        guard viewSize.width > 1, viewSize.height > 1 else { return nil }

        // Backend contract: x,y normalized 0…1 (top-left origin of captured frame).
        // UIKit points: origin top-left as well → direct map is fine for demo.
        let screenPoint = CGPoint(
            x: CGFloat(annotation.x) * viewSize.width,
            y: CGFloat(annotation.y) * viewSize.height
        )

        guard let worldTransform = raycastWorldTransform(from: screenPoint) else {
            // Fallback: place ~1.2m in front of camera, slightly down — keeps demo alive.
            return placeFallback(annotation)
        }

        let anchor = AnchorEntity(world: worldTransform)
        anchor.name = "ann:\(annotation.label)"
        let visual = RealityKitEntities.makeEntity(for: annotation)
        // Nudge slightly along surface normal (approx +Y after plane hit) so it isn't z-fighting.
        visual.position += SIMD3(0, 0.01, 0)
        anchor.addChild(visual)
        arView.scene.addAnchor(anchor)

        placedAnchors.append(anchor)
        labelToAnchor[annotation.label] = anchor
        return anchor
    }

    func clearAnnotations() {
        for anchor in placedAnchors {
            anchor.removeFromParent()
        }
        placedAnchors.removeAll()
        labelToAnchor.removeAll()
        annotationRoot.children.forEach { $0.removeFromParent() }
    }

    /// Tap at a screen point: prefer selecting an existing annotation, else place debug sphere.
    func handleTap(at screenPoint: CGPoint) {
        guard let arView else { return }

        // 1) Entity hit-test (select ELCB highlight / arrow)
        let hits = arView.hitTest(screenPoint, query: .nearest, mask: .all)
        if let entity = hits.first?.entity {
            if let label = nearestAnnotationLabel(from: entity) {
                onAnnotationSelected?(label)
                pulse(entity: entity)
                return
            }
        }

        // 2) Otherwise raycast to world and drop a debug marker (useful while wiring).
        if let transform = raycastWorldTransform(from: screenPoint) {
            let anchor = AnchorEntity(world: transform)
            anchor.addChild(RealityKitEntities.makeDebugSphere())
            arView.scene.addAnchor(anchor)
            placedAnchors.append(anchor)
        }
    }

    /// Raycast only — returns world transform if something is hit.
    func raycastWorldTransform(from screenPoint: CGPoint) -> simd_float4x4? {
        guard let arView else { return nil }

        // Prefer existing geometry (LiDAR mesh / planes) for stability.
        let existing = arView.raycast(
            from: screenPoint,
            allowing: .existingPlaneGeometry,
            alignment: .any
        )
        if let result = existing.first {
            return result.worldTransform
        }

        // Estimated planes fill gaps while mesh is still building.
        let estimated = arView.raycast(
            from: screenPoint,
            allowing: .estimatedPlane,
            alignment: .any
        )
        if let result = estimated.first {
            return result.worldTransform
        }

        // Last resort: scene raycast against RealityKit collision meshes (scene understanding).
        if let ray = arView.ray(through: screenPoint) {
            let rkHits = arView.scene.raycast(origin: ray.origin, direction: ray.direction)
            if let hit = rkHits.first {
                var t = matrix_identity_float4x4
                t.columns.3 = SIMD4(hit.position.x, hit.position.y, hit.position.z, 1)
                return t
            }
        }

        return nil
    }

    // MARK: - Private

    private func placeFallback(_ annotation: ARAnnotation) -> AnchorEntity? {
        guard let arView, let frame = arView.session.currentFrame else { return nil }

        let cam = frame.camera.transform
        // 1.0–1.4m forward from camera, with slight vertical bias from y.
        let forward = SIMD3(-cam.columns.2.x, -cam.columns.2.y, -cam.columns.2.z)
        let position = SIMD3(cam.columns.3.x, cam.columns.3.y, cam.columns.3.z)
            + normalize(forward) * 1.2
            + SIMD3(0, Float(0.3 - annotation.y) * 0.4, 0)

        var transform = matrix_identity_float4x4
        transform.columns.3 = SIMD4(position.x, position.y, position.z, 1)

        let anchor = AnchorEntity(world: transform)
        anchor.name = "ann-fallback:\(annotation.label)"
        anchor.addChild(RealityKitEntities.makeEntity(for: annotation))
        arView.scene.addAnchor(anchor)
        placedAnchors.append(anchor)
        labelToAnchor[annotation.label] = anchor
        return anchor
    }

    private func nearestAnnotationLabel(from entity: Entity) -> String? {
        var current: Entity? = entity
        while let node = current {
            if let name = optionalName(node.name), name.hasPrefix("ann:") {
                return String(name.dropFirst(4))
            }
            // Visual names: "highlight:ELCB", "arrow:ELCB", ...
            if let name = optionalName(node.name) {
                for prefix in ["highlight:", "arrow:", "circle:", "text:"] {
                    if name.hasPrefix(prefix) {
                        return String(name.dropFirst(prefix.count))
                    }
                }
            }
            current = node.parent
        }
        return nil
    }

    private func optionalName(_ name: String) -> String? {
        name.isEmpty ? nil : name
    }

    private func pulse(entity: Entity) {
        var target = entity
        // Prefer the model root we named.
        while let parent = target.parent, parent is ModelEntity || parent.name.contains(":") {
            if parent.name.contains(":") { target = parent; break }
            target = parent
        }
        let original = target.scale
        target.scale = original * 1.15
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            target.scale = original
        }
    }
}

// MARK: - Math

private func normalize(_ v: SIMD3<Float>) -> SIMD3<Float> {
    let len = simd_length(v)
    guard len > 1e-5 else { return SIMD3(0, 0, -1) }
    return v / len
}
