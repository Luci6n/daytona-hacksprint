//
//  ARSessionManager.swift
//  DaddyFix
//
//  Brian — ARKit + LiDAR session lifecycle.
//

import ARKit
import Combine
import Foundation
import RealityKit
import SwiftUI

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

        runSession()
    }

    func runSession() {
        guard ARWorldTrackingConfiguration.isSupported else {
            trackingStatus = .notAvailable
            return
        }

        let config = ARWorldTrackingConfiguration()
        config.planeDetection = [.horizontal, .vertical]
        config.environmentTexturing = .automatic
        config.worldAlignment = .gravity

        // LiDAR scene reconstruction — the demo differentiator.
        if ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh) {
            config.sceneReconstruction = .mesh
            isLiDARAvailable = true
            meshEnabled = true
        } else if ARWorldTrackingConfiguration.supportsSceneReconstruction(.meshWithClassification) {
            config.sceneReconstruction = .meshWithClassification
            isLiDARAvailable = true
            meshEnabled = true
        } else {
            isLiDARAvailable = false
            meshEnabled = false
            // Still usable on non-LiDAR devices via plane estimation.
        }

        // Frame semantics help depth-aware placement when available.
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            config.frameSemantics.insert(.sceneDepth)
        }
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.smoothedSceneDepth) {
            config.frameSemantics.insert(.smoothedSceneDepth)
        }

        arView?.session.run(config, options: [.resetTracking, .removeExistingAnchors])
        trackingStatus = .initializing
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
