//
//  ARSessionManager.swift
//  DaddyFix
//
//  Brian — ARKit + LiDAR session lifecycle.
//

import ARKit
import Combine
import CoreImage
import CoreVideo
import Foundation
import RealityKit
import SwiftUI
import UIKit

/// Owns the AR session configuration (LiDAR mesh + planes) and tracking status.
@MainActor
final class ARSessionManager: NSObject, ObservableObject {
    enum TrackingStatus: String {
        case initializing = "Starting LiDAR…"
        case normal = "LiDAR tracking"
        case limited = "Tracking limited — move slowly"
        case notAvailable = "AR not available on this device"
        case relocalizing = "Re-anchoring…"
    }

    @Published private(set) var trackingStatus: TrackingStatus = .initializing
    @Published private(set) var isLiDARAvailable: Bool = false
    @Published private(set) var meshEnabled: Bool = false
    @Published private(set) var planeCount: Int = 0

    /// Weak ref to the live ARView (set by ARViewContainer).
    private(set) weak var arView: ARView?

    private var planeAnchors: [UUID: ARPlaneAnchor] = [:]

    // MARK: - Attach / configure

    func attach(arView: ARView) {
        self.arView = arView
        arView.session.delegate = self
        arView.automaticallyConfigureSession = false

        // Soft environment for readable labels on appliances.
        arView.renderOptions.insert(.disableMotionBlur)
        arView.environment.background = .cameraFeed()

        #if DEBUG
        // Optional: visualize feature points while developing.
        // arView.debugOptions = [.showFeaturePoints]
        #endif

        // IMPORTANT: do not mutate @Published state synchronously inside
        // UIViewRepresentable.makeUIView (SwiftUI view-update cycle).
        // Defer so we don't get:
        // "Publishing changes from within view updates is not allowed".
        Task { @MainActor in
            self.runSession()
        }
    }

    func runSession() {
        guard ARWorldTrackingConfiguration.isSupported else {
            publish {
                self.trackingStatus = .notAvailable
            }
            return
        }

        let config = ARWorldTrackingConfiguration()
        config.planeDetection = [.horizontal, .vertical]
        config.environmentTexturing = .automatic
        config.worldAlignment = .gravity

        var lidar = false
        var mesh = false

        // LiDAR scene reconstruction — the demo differentiator.
        if ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh) {
            config.sceneReconstruction = .mesh
            lidar = true
            mesh = true
        } else if ARWorldTrackingConfiguration.supportsSceneReconstruction(.meshWithClassification) {
            config.sceneReconstruction = .meshWithClassification
            lidar = true
            mesh = true
        }
        // else: still usable on non-LiDAR devices via plane estimation.

        // Frame semantics help depth-aware placement when available.
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            config.frameSemantics.insert(.sceneDepth)
        }
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.smoothedSceneDepth) {
            config.frameSemantics.insert(.smoothedSceneDepth)
        }

        arView?.session.run(config, options: [.resetTracking, .removeExistingAnchors])

        publish {
            self.isLiDARAvailable = lidar
            self.meshEnabled = mesh
            self.trackingStatus = .initializing
        }
    }

    /// Coalesce UI publishes onto the next main-actor turn (safe from view updates).
    private func publish(_ updates: @escaping @MainActor () -> Void) {
        Task { @MainActor in
            updates()
        }
    }

    func pause() {
        arView?.session.pause()
    }

    func resume() {
        runSession()
    }

    /// Toggle mesh visualization for the “watch LiDAR map the scene” demo beat.
    func setMeshVisualizationEnabled(_ enabled: Bool) {
        guard let arView else { return }
        if enabled, meshEnabled {
            arView.debugOptions.insert(.showSceneUnderstanding)
        } else {
            arView.debugOptions.remove(.showSceneUnderstanding)
        }
    }

    /// Snapshot the live AR camera for Lucian `POST /analyze` (JPEG).
    /// Prefers `ARFrame.capturedImage` (CVPixelBuffer → UIImage).
    func captureFrameImage() -> UIImage? {
        guard let frame = arView?.session.currentFrame else { return nil }
        return UIImage(pixelBuffer: frame.capturedImage)
    }
}

// MARK: - CVPixelBuffer → UIImage

private extension UIImage {
    convenience init?(pixelBuffer: CVPixelBuffer) {
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let context = CIContext(options: nil)
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else {
            return nil
        }
        // ARKit buffer is landscape-right relative to portrait UI; rotate for upright JPEG.
        self.init(cgImage: cgImage, scale: 1.0, orientation: .right)
    }
}

// MARK: - ARSessionDelegate

extension ARSessionManager: ARSessionDelegate {
    nonisolated func session(_ session: ARSession, didAdd anchors: [ARAnchor]) {
        Task { @MainActor in
            for anchor in anchors {
                if let plane = anchor as? ARPlaneAnchor {
                    planeAnchors[plane.identifier] = plane
                }
            }
            planeCount = planeAnchors.count
        }
    }

    nonisolated func session(_ session: ARSession, didUpdate anchors: [ARAnchor]) {
        Task { @MainActor in
            for anchor in anchors {
                if let plane = anchor as? ARPlaneAnchor {
                    planeAnchors[plane.identifier] = plane
                }
            }
            planeCount = planeAnchors.count
        }
    }

    nonisolated func session(_ session: ARSession, didRemove anchors: [ARAnchor]) {
        Task { @MainActor in
            for anchor in anchors {
                planeAnchors.removeValue(forKey: anchor.identifier)
            }
            planeCount = planeAnchors.count
        }
    }

    nonisolated func session(_ session: ARSession, cameraDidChangeTrackingState camera: ARCamera) {
        Task { @MainActor in
            switch camera.trackingState {
            case .notAvailable:
                trackingStatus = .notAvailable
            case .limited(let reason):
                switch reason {
                case .relocalizing:
                    trackingStatus = .relocalizing
                default:
                    trackingStatus = .limited
                }
            case .normal:
                trackingStatus = .normal
            @unknown default:
                trackingStatus = .limited
            }
        }
    }

    nonisolated func session(_ session: ARSession, didFailWithError error: Error) {
        Task { @MainActor in
            trackingStatus = .notAvailable
            print("[ARSessionManager] Session failed: \(error.localizedDescription)")
        }
    }

    nonisolated func sessionWasInterrupted(_ session: ARSession) {
        Task { @MainActor in
            trackingStatus = .relocalizing
        }
    }

    nonisolated func sessionInterruptionEnded(_ session: ARSession) {
        Task { @MainActor in
            // Re-run to recover world map quality after interruption.
            runSession()
        }
    }
}
