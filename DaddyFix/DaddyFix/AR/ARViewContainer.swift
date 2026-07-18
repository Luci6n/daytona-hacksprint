//
//  ARViewContainer.swift
//  DaddyFix
//
//  Brian — SwiftUI bridge for RealityKit ARView + tap handling.
//

import ARKit
import RealityKit
import SwiftUI

/// Embed this in Lucian’s ContentView. Owns AR session + raycast wiring.
struct ARViewContainer: UIViewRepresentable {
    @ObservedObject var sessionManager: ARSessionManager
    var raycastManager: RaycastManager

    /// When true, shows LiDAR scene-understanding mesh (great for demo narration).
    var showMeshOverlay: Bool = false

    /// Optional: place mock water-heater annotations after a short delay (local Brian test).
    var autoPlaceMockAnnotations: Bool = false

    func makeCoordinator() -> Coordinator {
        Coordinator(
            sessionManager: sessionManager,
            raycastManager: raycastManager
        )
    }

    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        arView.contentScaleFactor = UIScreen.main.scale

        // Coaching: helps judges get tracking quickly before ELCB placement.
        let coaching = ARCoachingOverlayView()
        coaching.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        coaching.session = arView.session
        coaching.goal = .anyPlane
        coaching.activatesAutomatically = true
        arView.addSubview(coaching)
        coaching.frame = arView.bounds

        sessionManager.attach(arView: arView)
        raycastManager.attach(arView: arView)

        let tap = UITapGestureRecognizer(
            target: context.coordinator,
            action: #selector(Coordinator.handleTap(_:))
        )
        arView.addGestureRecognizer(tap)

        context.coordinator.arView = arView

        if autoPlaceMockAnnotations {
            // Wait for planes/mesh to warm up, then drop hero annotations.
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                raycastManager.placeAnnotations(AnalysisResult.waterHeaterMock.arAnnotations)
            }
        }

        return arView
    }

    func updateUIView(_ uiView: ARView, context: Context) {
        sessionManager.setMeshVisualizationEnabled(showMeshOverlay)
    }

    static func dismantleUIView(_ uiView: ARView, coordinator: Coordinator) {
        coordinator.sessionManager.pause()
    }

    // MARK: - Coordinator

    final class Coordinator: NSObject {
        let sessionManager: ARSessionManager
        let raycastManager: RaycastManager
        weak var arView: ARView?

        init(sessionManager: ARSessionManager, raycastManager: RaycastManager) {
            self.sessionManager = sessionManager
            self.raycastManager = raycastManager
        }

        @objc func handleTap(_ gesture: UITapGestureRecognizer) {
            guard let arView, gesture.state == .ended else { return }
            let point = gesture.location(in: arView)
            raycastManager.handleTap(at: point)
        }
    }
}

// MARK: - Convenience host (Brian local harness)

/// Temporary full-screen AR host so Brian can run/test without Lucian’s UI yet.
/// Lucian will replace `ContentView` with the real shell and embed `ARViewContainer`.
struct ARDebugHostView: View {
    @StateObject private var sessionManager = ARSessionManager()
    @State private var raycastManager = RaycastManager()
    @State private var showMesh = false
    @State private var selectedLabel: String?
    @State private var statusMessage: String = "Point at the water heater / any vertical surface"

    var body: some View {
        ZStack {
            ARViewContainer(
                sessionManager: sessionManager,
                raycastManager: raycastManager,
                showMeshOverlay: showMesh,
                autoPlaceMockAnnotations: true
            )
            .ignoresSafeArea()

            VStack {
                HStack {
                    statusChip
                    Spacer()
                    Toggle(isOn: $showMesh) {
                        Text("LiDAR mesh")
                            .font(.caption.weight(.semibold))
                    }
                    .toggleStyle(.button)
                    .padding(8)
                    .background(.ultraThinMaterial, in: Capsule())
                }
                .padding()

                Spacer()

                VStack(spacing: 10) {
                    if let selectedLabel {
                        Text("Selected: \(selectedLabel)")
                            .font(.headline)
                    }
                    Text(statusMessage)
                        .font(.footnote)
                        .multilineTextAlignment(.center)

                    HStack(spacing: 12) {
                        Button("Place mock ELCB") {
                            raycastManager.placeAnnotations(AnalysisResult.waterHeaterMock.arAnnotations)
                            statusMessage = "Placed mock annotations — walk around; they should stay locked."
                        }
                        .buttonStyle(ARChromeButtonStyle())

                        Button("Clear") {
                            raycastManager.clearAnnotations()
                            selectedLabel = nil
                            statusMessage = "Cleared. Tap a surface to drop a debug sphere."
                        }
                        .buttonStyle(ARChromeButtonStyle(filled: false))
                    }
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(.ultraThinMaterial)
            }
        }
        .onAppear {
            raycastManager.onAnnotationSelected = { label in
                selectedLabel = label
                statusMessage = "Tapped \(label) — Lucian will open guide / buy flow here."
            }
        }
    }

    private var statusChip: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            VStack(alignment: .leading, spacing: 2) {
                Text(sessionManager.trackingStatus.rawValue)
                    .font(.caption.weight(.semibold))
                Text(sessionManager.isLiDARAvailable ? "LiDAR ready" : "No LiDAR — planes only")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial, in: Capsule())
    }

    private var statusColor: Color {
        switch sessionManager.trackingStatus {
        case .normal: return .green
        case .initializing, .relocalizing: return .yellow
        case .limited: return .orange
        case .notAvailable: return .red
        }
    }
}

private struct ARChromeButtonStyle: ButtonStyle {
    var filled: Bool = true

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.subheadline.weight(.semibold))
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(
                Capsule().fill(filled ? Color.accentColor.opacity(configuration.isPressed ? 0.7 : 1) : Color.clear)
            )
            .overlay(
                Capsule().strokeBorder(Color.primary.opacity(0.25), lineWidth: filled ? 0 : 1)
            )
            .foregroundStyle(filled ? Color.white : Color.primary)
    }
}
